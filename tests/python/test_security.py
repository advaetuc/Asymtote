"""Production security controls, privacy, bounded reception and CPU checkpoints."""

import asyncio
import json
import logging

import pytest
from fastapi.testclient import TestClient

from api_app import create_app, observability, services
from solver_core.budget import check_budget, computation_budget
from solver_core.gaussian import solve_gaussian
from solver_core.models import ArithmeticMode
from solver_core.parsing import parse_system

PAYLOAD = {"system": {"a": [["1"]], "b": ["2"]}, "method": "gaussian"}


@pytest.mark.parametrize("path", ["/api/health", "/api/absent", "/api/openapi.json"])
def test_headers_on_api_success_and_failure(path):
    response = TestClient(create_app()).get(path)
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
    assert "camera=()" in response.headers["permissions-policy"]
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "headers",
    [
        {"origin": "https://evil.example"},
        {"origin": "null"},
        {"origin": "http://testserver.evil.example"},
        {"origin": "http://testserver", "sec-fetch-site": "same-site"},
        {"sec-fetch-site": "cross-site"},
        {"origin": "https://evil.example", "x-forwarded-host": "evil.example"},
    ],
)
def test_cross_origin_posts_are_rejected_before_solver(headers, monkeypatch):
    monkeypatch.setattr(services, "solve", lambda *args: pytest.fail("Solver must not run"))
    response = TestClient(create_app()).post("/api/v1/solve", json=PAYLOAD, headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "origin_rejected"
    assert "evil" not in response.text


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"origin": "http://testserver"},
        {"origin": "http://localhost:3000", "sec-fetch-site": "same-origin"},
    ],
)
def test_same_origin_and_command_line_requests_are_supported(headers):
    response = TestClient(create_app()).post("/api/v1/solve", json=PAYLOAD, headers=headers)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"origin": "https://augmentr-solvr.vercel.app"},
        {"origin": "https://augmentr-solvr.vercel.app", "sec-fetch-site": "same-origin"},
    ],
)
def test_augmentr_host_accepts_its_own_origin_and_cli_requests(headers):
    client = TestClient(create_app(), base_url="https://augmentr-solvr.vercel.app")
    response = client.post("/api/v1/solve", json=PAYLOAD, headers=headers)
    assert response.status_code == 200
    assert response.json()["result"]["classification"]["classification"] == "unique"
    assert response.json()["result"]["solution"] == [2.0]
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "headers",
    [
        {"origin": "https://asymtote.vercel.app"},
        {"origin": "https://augmentr.vercel.app"},
        {"origin": "https://asymtote.vercel.app", "sec-fetch-site": "cross-site"},
        {"origin": "https://asymtote.vercel.app", "sec-fetch-site": "same-site"},
        {"origin": "https://asymtote.vercel.app", "x-forwarded-host": "asymtote.vercel.app"},
        {"origin": "https://evil.example"},
        {"origin": "https://augmentr-solvr.vercel.app.evil.example"},
        {"origin": "http://augmentr-solvr.vercel.app"},
        {"origin": "https://augmentr-solvr.vercel.app:444"},
        {"origin": "https://augmentr-solvr.vercel.app", "sec-fetch-site": "cross-site"},
        {"origin": "https://augmentr-solvr.vercel.app", "sec-fetch-site": "same-site"},
    ],
)
def test_augmentr_host_rejects_other_origins_before_solving(headers, monkeypatch):
    monkeypatch.setattr(services, "solve", lambda *args: pytest.fail("Solver must not run"))
    client = TestClient(create_app(), base_url="https://augmentr-solvr.vercel.app")
    response = client.post("/api/v1/solve", json=PAYLOAD, headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "origin_rejected"
    assert "access-control-allow-origin" not in response.headers


def test_rejected_keys_values_query_paths_and_exception_messages_do_not_leak(monkeypatch):
    events = []

    class Capture(logging.Handler):
        def emit(self, record):
            events.append(record.getMessage())

    capture = Capture()
    observability.LOGGER.addHandler(capture)
    try:
        client = TestClient(create_app())
        secret = "sensitive-user-token"
        response = client.post("/api/v1/solve?token=" + secret, json={**PAYLOAD, secret: secret})
        assert response.status_code == 422
        assert response.json()["details"][0]["location"][-1] == "unknown_field"
        assert secret not in response.text
        response = client.get("/api/" + secret)
        assert secret not in response.text

        def fail(*args):
            raise RuntimeError(secret)

        monkeypatch.setattr(services, "solve", fail)
        response = client.post("/api/v1/solve", json=PAYLOAD)
        assert response.status_code == 500
        assert secret not in response.text
        assert all(secret not in event and "Traceback" not in event for event in events)
        assert len(events) == 3
    finally:
        observability.LOGGER.removeHandler(capture)


def test_body_deadline_handles_slow_chunked_upload(monkeypatch):
    monkeypatch.setattr(observability, "BODY_TIMEOUT_SECONDS", 0.01)
    messages = []
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/solve",
        "headers": [],
        "scheme": "http",
        "query_string": b"",
        "server": ("localhost", 18000),
    }

    async def receive():
        await asyncio.sleep(0.1)
        return {"type": "http.request", "body": b"", "more_body": True}

    async def send(message):
        messages.append(message)

    asyncio.run(create_app()(scope, receive, send))
    assert messages[0]["status"] == 408
    assert json.loads(messages[1]["body"])["error"]["code"] == "request_timeout"


def test_request_deadline_and_cpu_timeout_are_generic(monkeypatch):
    monkeypatch.setattr(observability, "REQUEST_TIMEOUT_SECONDS", 0.01)
    app = create_app()

    @app.get("/test-timeout")
    async def slow():
        await asyncio.sleep(0.1)

    assert TestClient(app).get("/test-timeout").status_code == 504

    def cpu_timeout(*args):
        raise TimeoutError("private input")

    monkeypatch.setattr(services, "solve", cpu_timeout)
    response = TestClient(app).post("/api/v1/solve", json=PAYLOAD)
    assert response.status_code == 504
    assert "private input" not in response.text
    assert response.headers["x-request-id"] == response.json()["request_id"]


def test_cpu_budget_is_scoped_and_interrupts_exact_elimination(monkeypatch):
    from solver_core import budget

    now = [1.0]
    monkeypatch.setattr(budget.time, "monotonic", lambda: now[0])
    system = parse_system([["1"]], ["2"], mode=ArithmeticMode.EXACT)
    with computation_budget(1):
        now[0] = 3.0
        with pytest.raises(TimeoutError):
            solve_gaussian(system)
        now[0] = 1.0
    now[0] = 100.0
    check_budget()


def test_production_disables_remote_swagger_assets(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    client = TestClient(create_app())
    response = client.get("/api/docs")
    assert response.status_code == 404
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
    assert client.get("/api/openapi.json").status_code == 200
