"""Real ASGI contract, error, observability, and schema-generation coverage."""

import asyncio
import copy
import json
import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api_app import create_app, services
from api_app.observability import LOGGER, MAX_REQUEST_BODY_BYTES
from scripts.export_openapi import export_openapi
from solver_core.errors import ErrorCode, NumericBreakdownError, ResourceLimitError

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = {"a": [["4", "1"], ["2", "3"]], "b": ["1", "2"]}


@pytest.fixture
def client():
    with TestClient(create_app()) as value:
        yield value


@pytest.fixture
def events():
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(json.loads(record.getMessage()))

    handler = Capture()
    LOGGER.addHandler(handler)
    yield records
    LOGGER.removeHandler(handler)


def request_payload(method="gaussian", system=None, options=None):
    result = {"system": copy.deepcopy(SYSTEM if system is None else system), "method": method}
    if options is not None:
        result["options"] = options
    return result


def assert_safe_json(response):
    json.loads(response.text, parse_constant=lambda value: pytest.fail(f"Nonfinite JSON: {value}"))
    assert response.headers["content-type"] == "application/json"
    assert response.headers["x-request-id"] == response.json()["request_id"]


def test_analyze_unique_system_and_method_diagnostics(client):
    response = client.post("/api/v1/analyze", json={"system": SYSTEM})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "analyzed"
    assert data["shape"] == {"equations": 2, "unknowns": 2}
    assert data["is_square"]
    assert data["classification"]["rank_a"] == data["classification"]["rank_augmented"] == 2
    assert data["classification"]["classification"] == "unique"
    assert data["conditioning"]["status"] == "finite"
    assert data["strict_diagonal_dominance"]
    methods = {item["method"]: item for item in data["methods"]}
    assert set(methods) == {"gaussian", "gauss_jordan", "jacobi", "gauss_seidel"}
    assert all(item["eligible"] for item in methods.values())
    assert methods["jacobi"]["convergence"]["spectral"]["radius"] == pytest.approx((1 / 6) ** 0.5)
    assert methods["gauss_seidel"]["convergence"]["spectral"]["radius"] == pytest.approx(1 / 6)
    assert_safe_json(response)


@pytest.mark.parametrize(
    "system,kind",
    [
        ({"a": [["1", "1"]], "b": ["2"]}, "infinite"),
        ({"a": [["1"], ["1"]], "b": ["2", "2"]}, "unique"),
        ({"a": [["1"], ["1"]], "b": ["2", "3"]}, "inconsistent"),
    ],
)
def test_analyze_rectangular_systems_and_eligibility(client, system, kind):
    response = client.post("/api/v1/analyze", json={"system": system})
    assert response.status_code == 200
    data = response.json()
    assert not data["is_square"]
    assert data["classification"]["classification"] == kind
    assert data["strict_diagonal_dominance"] is None
    assert data["dominance_permutation"] is data["nonzero_permutation"] is None
    for item in data["methods"]:
        assert item["eligible"] == (item["method"] in ("gaussian", "gauss_jordan"))


def test_exact_analysis_labels_floating_conditioning_and_iterative_reanalysis(client):
    data = client.post(
        "/api/v1/analyze", json={"system": SYSTEM, "arithmetic_mode": "exact"}
    ).json()
    assert data["classification"]["arithmetic_mode"] == "exact"
    assert data["classification"]["rank_tolerance"] is None
    assert data["conditioning_arithmetic_mode"] == "float64"
    assert data["warnings"]
    assert [item["code"] for item in data["methods"][-2:]] == ["requires_float64"] * 2


def test_analysis_suggests_row_mapping_without_mutating_source(client):
    system = {"a": [["0", "4"], ["3", "1"]], "b": ["8", "5"]}
    original = copy.deepcopy(system)
    data = client.post("/api/v1/analyze", json={"system": system}).json()
    assert data["dominance_permutation"]["order"] == [1, 0]
    assert not data["strict_diagonal_dominance"]
    assert data["methods"][-1]["requires_row_reordering"]
    assert system == original


def test_analysis_exposes_nonzero_fallback_and_risk_as_separate_requirements(client):
    system = {"a": [["0", "1", "1"], ["1", "1", "0"], ["1", "0", "1"]], "b": ["2"] * 3}
    data = client.post("/api/v1/analyze", json={"system": system}).json()
    assert data["dominance_permutation"] is None
    assert data["nonzero_permutation"] is not None
    for item in data["methods"][-2:]:
        assert item["eligible"] and item["requires_row_reordering"]
        assert item["row_permutation"]["purpose"] == "nonzero_diagonal"


@pytest.mark.parametrize("method", ["gaussian", "gauss_jordan"])
@pytest.mark.parametrize("mode", ["float64", "exact"])
def test_direct_solve_contract_has_complete_trace_and_report_metadata(client, method, mode):
    payload = request_payload(method, options={"arithmetic_mode": mode})
    payload["display"] = {"mode": "fraction", "decimal_places": 4}
    response = client.post("/api/v1/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["method"] == method and result["arithmetic_mode"] == mode
    assert result["trace"] and result["diagnostics"] is not None
    assert result["classification"]["classification"] == "unique"
    assert data["report"]["method"] == method
    assert data["report"]["display"] == payload["display"]
    assert data["report"]["fraction_values"] == ("exact" if mode == "exact" else "approximate")
    assert "trace" not in data["report"]
    if mode == "exact":
        assert result["solution"] == [
            {"numerator": "1", "denominator": "10"},
            {"numerator": "3", "denominator": "5"},
        ]
        for row in data["problem"]["original_system"]["a"]:
            assert all(isinstance(value["numerator"], str) for value in row)
    else:
        assert result["solution"] == pytest.approx([0.1, 0.6])
    assert_safe_json(response)


def test_exact_wire_format_preserves_javascript_unsafe_integer(client):
    system = {"a": [["9007199254740993/10000"]], "b": ["1"]}
    data = client.post(
        "/api/v1/solve", json=request_payload("gaussian", system, {"arithmetic_mode": "exact"})
    ).json()
    assert data["result"]["solution"] == [{"numerator": "10000", "denominator": "9007199254740993"}]


@pytest.mark.parametrize("method", ["gaussian", "gauss_jordan"])
@pytest.mark.parametrize("b,kind", [(["2", "2"], "infinite"), (["2", "3"], "inconsistent")])
def test_direct_mathematical_outcomes_are_http_success(client, method, b, kind):
    response = client.post(
        "/api/v1/solve", json=request_payload(method, {"a": [["1", "1"], ["1", "1"]], "b": b})
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["classification"]["classification"] == kind
    assert result["solution"] is None
    assert (result["parametric_solution"] is not None) == (kind == "infinite")
    assert bool(result["contradictory_rows"]) == (kind == "inconsistent")
    assert_safe_json(response)


@pytest.mark.parametrize("method", ["jacobi", "gauss_seidel"])
def test_iterative_solve_default_and_custom_options(client, method):
    converged = client.post("/api/v1/solve", json=request_payload(method))
    assert converged.status_code == 200
    assert converged.json()["result"]["status"] == "converged"
    options = {"initial_guess": ["1/3", "1e-1"], "tolerance": 1e-10, "max_iterations": 1}
    response = client.post("/api/v1/solve", json=request_payload(method, options=options))
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "max_iterations_reached"
    assert result["initial_guess"] == [float(Fraction(1, 3)), 0.1]
    assert result["solution"] is None and len(result["history"]) == 1
    assert result["last_iterate"] == result["history"][-1]["vector"]
    assert result["diagnostics"]["residual_inf"] == result["history"][-1]["residual_inf"]
    assert response.json()["report"]["options"]["initial_guess"] == ["1/3", "1e-1"]
    assert_safe_json(response)


@pytest.mark.parametrize("method", ["jacobi", "gauss_seidel"])
def test_iterative_row_mapping_is_returned(client, method):
    system = {"a": [["0", "4"], ["3", "1"]], "b": ["8", "5"]}
    data = client.post("/api/v1/solve", json=request_payload(method, system)).json()
    assert data["result"]["reordering"]["permutation"]["order"] == [1, 0]
    assert data["result"]["solution"] == pytest.approx([1, 2])
    assert data["problem"]["original_system"]["a"] == [[0, 4], [3, 1]]


@pytest.mark.parametrize("method", ["jacobi", "gauss_seidel"])
def test_risk_decline_override_and_numeric_breakdown_are_typed_200(client, method):
    system = {"a": [["1", "100"], ["100", "1"]], "b": ["1", "1"]}
    options = {"auto_reorder_for_diagonal_dominance": False}
    data = client.post("/api/v1/solve", json=request_payload(method, system, options)).json()
    assert data["result"]["status"] == "convergence_risk_declined"
    assert data["result"]["history"] == []
    options.update(run_despite_convergence_risk=True, max_iterations=500)
    response = client.post("/api/v1/solve", json=request_payload(method, system, options))
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "numeric_breakdown" and result["history"]
    assert result["solution"] is None and result["breakdown_reason"]
    assert_safe_json(response)


@pytest.mark.parametrize("route", ["analyze", "solve"])
@pytest.mark.parametrize(
    "system",
    [
        {"a": [], "b": []},
        {"a": [["1"]], "b": []},
        {"a": [["1", "2"], ["3"]], "b": ["1", "2"]},
        {"a": [["1"], ["2"]], "b": ["1"]},
        {"a": [["1"]] * 13, "b": ["1"] * 13},
        {"a": [["1"] * 13], "b": ["1"]},
        {"a": [[1]], "b": ["1"]},
        {"a": [[True]], "b": ["1"]},
        {"a": [["1"]], "b": [1.5]},
        {"a": "1", "b": ["1"]},
        {"a": [["1"]], "b": ["1"], "secret": "extra"},
    ],
)
def test_invalid_system_contract_returns_sanitized_422(client, route, system):
    payload = {"system": system} if route == "analyze" else request_payload(system=system)
    response = client.post("/api/v1/" + route, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["details"]
    assert "input" not in response.json()["details"][0]
    assert_safe_json(response)


@pytest.mark.parametrize(
    "token",
    [
        "",
        " 1",
        "1 ",
        "NaN",
        "Inf",
        "1/0",
        "1e101",
        "1e-101",
        "1000000000001",
        "1" * 49,
        "__import__('os')",
        "2+2",
        "１",
        "0x1",
    ],
)
def test_invalid_token_grammar_is_reused_at_api_boundary(client, token):
    response = client.post("/api/v1/analyze", json={"system": {"a": [[token]], "b": ["1"]}})
    assert response.status_code == 422
    assert response.json()["details"][0]["location"] == ["body", "system", "a", 0, 0]
    assert_safe_json(response)


@pytest.mark.parametrize(
    "method,options",
    [
        ("gaussian", {"max_iterations": 2}),
        ("gauss_jordan", {"tolerance": 1e-8}),
        ("gaussian", {"arithmetic_mode": "decimal"}),
        ("jacobi", {"arithmetic_mode": "exact"}),
        ("jacobi", {"max_iterations": 501}),
        ("gauss_seidel", {"max_iterations": 0}),
        ("jacobi", {"max_iterations": True}),
        ("gauss_seidel", {"max_iterations": "25"}),
        ("jacobi", {"tolerance": "1e-8"}),
        ("gauss_seidel", {"tolerance": 1e-15}),
        ("jacobi", {"tolerance": 0.1}),
        ("jacobi", {"auto_reorder_for_diagonal_dominance": "yes"}),
        ("jacobi", {"initial_guess": [0, 0]}),
        ("jacobi", {"initial_guess": ["0"]}),
        ("gauss_seidel", {"initial_guess": ["1/0", "0"]}),
        ("unknown", {}),
    ],
)
def test_method_specific_options_cannot_be_coerced_or_mixed(client, method, options):
    response = client.post("/api/v1/solve", json=request_payload(method, options=options))
    assert response.status_code == 422


@pytest.mark.parametrize(
    "display",
    [{"decimal_places": 13}, {"decimal_places": -1}, {"decimal_places": True}, {"mode": "latex"}],
)
def test_display_preferences_are_bounded(client, display):
    payload = request_payload()
    payload["display"] = display
    assert client.post("/api/v1/solve", json=payload).status_code == 422


def test_display_does_not_round_computation(client):
    payload = request_payload("jacobi", options={"max_iterations": 1})
    payload["display"] = {"decimal_places": 0}
    result = client.post("/api/v1/solve", json=payload).json()["result"]
    assert result["history"][0]["vector"][1] == 2 / 3


@pytest.mark.parametrize(
    "body",
    [
        "{",
        "null",
        "[]",
        '{"system": {}}',
        '{"method":"jacobi","system":{"a":[["1"]],"b":["1"]},"options":{"tolerance":NaN}}',
    ],
)
def test_malformed_json_and_nonfinite_json_have_safe_validation_responses(client, body):
    response = client.post(
        "/api/v1/solve", content=body, headers={"content-type": "application/json"}
    )
    assert response.status_code == 422
    assert_safe_json(response)


@pytest.mark.parametrize(
    "system,options",
    [
        ({"a": [["1", "2"]], "b": ["1"]}, {}),
        ({"a": [["1", "1"], ["1", "1"]], "b": ["1", "1"]}, {}),
        (
            {"a": [["0", "1"], ["1", "0"]], "b": ["1", "1"]},
            {"auto_reorder_for_diagonal_dominance": False},
        ),
    ],
)
def test_ineligible_iteration_is_a_precondition_error(client, system, options):
    response = client.post("/api/v1/solve", json=request_payload("jacobi", system, options))
    assert response.status_code == 422
    assert response.json()["error"]["code"] in ("invalid_system", "zero_pivot")


@pytest.mark.parametrize("route", ["analyze", "solve"])
def test_controlled_rank_uncertainty_returns_a_mathematical_outcome(client, monkeypatch, route):
    def fail(*args):
        raise NumericBreakdownError(ErrorCode.RANK_UNCERTAIN, "Use exact mode or rescale.")

    monkeypatch.setattr(
        services, "classify_system" if route == "analyze" else "solve_gaussian", fail
    )
    payload = {"system": SYSTEM} if route == "analyze" else request_payload()
    response = client.post("/api/v1/" + route, json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "numeric_breakdown"
    assert response.json()["error"]["code"] == "rank_uncertain"
    assert_safe_json(response)


def test_exact_growth_limit_is_a_controlled_policy_error(client, monkeypatch):
    def fail(*args):
        raise ResourceLimitError(ErrorCode.RATIONAL_GROWTH_LIMIT, "Use float64 mode.")

    monkeypatch.setattr(services, "solve_gaussian", fail)
    response = client.post(
        "/api/v1/solve", json=request_payload(options={"arithmetic_mode": "exact"})
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "rational_growth_limit"


@pytest.mark.parametrize("route", ["analyze", "solve"])
def test_unexpected_exceptions_have_generic_500_and_correlated_private_logs(
    client, monkeypatch, events, route
):
    def fail(*args):
        raise RuntimeError("private-coefficient-12345 traceback secret")

    monkeypatch.setattr(services, route, fail)
    payload = {"system": SYSTEM} if route == "analyze" else request_payload()
    response = client.post(
        "/api/v1/" + route, json=payload, headers={"x-request-id": "test-request-42"}
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret" not in response.text and "traceback" not in response.text
    assert_safe_json(response)
    assert len(events) == 1
    assert events[0]["request_id"] == "test-request-42"
    assert events[0]["error_code"] == "internal_error"
    assert events[0]["exception_type"] == "RuntimeError"
    assert "private-coefficient" not in json.dumps(events)


def test_response_validation_failure_is_also_generic_500(client, monkeypatch):
    monkeypatch.setattr(services, "solve", lambda *args: {"unexpected": "private"})
    response = client.post("/api/v1/solve", json=request_payload())
    assert response.status_code == 500 and "private" not in response.text
    assert_safe_json(response)


def test_log_has_metadata_only_once_and_valid_correlation(client, events):
    system = {"a": [["12345.6789"]], "b": ["1"]}
    response = client.post(
        "/api/v1/solve",
        json=request_payload(system=system),
        headers={"x-request-id": "integration_1"},
    )
    assert len(events) == 1
    event = events[0]
    assert event["request_id"] == response.headers["x-request-id"] == "integration_1"
    assert event["method"] == "gaussian" and event["route"] == "/api/v1/solve"
    assert event["equations"] == event["unknowns"] == 1
    assert event["duration_ms"] >= 0 and event["http_status"] == 200
    assert event["result_status"] == "unique" and event["warning_codes"] == ["floating_tolerance"]
    assert "12345.6789" not in json.dumps(events)


@pytest.mark.parametrize("request_id", ["", "a" * 65, "unsafe id", "../input"])
def test_invalid_correlation_id_is_replaced(client, request_id):
    response = client.post(
        "/api/v1/solve", json=request_payload(), headers={"x-request-id": request_id}
    )
    assert len(response.headers["x-request-id"]) == 32
    assert response.headers["x-request-id"] != request_id


def test_concurrent_requests_have_independent_metadata(client, events):
    def run(i):
        response = client.post(
            "/api/v1/solve",
            json=request_payload(system={"a": [["1"]], "b": [str(i)]}),
            headers={"x-request-id": f"parallel-{i}"},
        )
        return response.json()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, range(8)))
    assert len(events) == 8
    for i, result in enumerate(results):
        assert result["request_id"] == f"parallel-{i}"
        assert result["result"]["solution"] == [i]


def test_oversize_body_is_rejected_before_json_parsing(client, events):
    response = client.post(
        "/api/v1/solve",
        content=" " * (MAX_REQUEST_BODY_BYTES + 1),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_too_large"
    assert len(events) == 1


def test_chunked_body_limit_does_not_trust_content_length():
    app = create_app()
    messages = []
    chunks = iter(
        [
            {"type": "http.request", "body": b" " * 40000, "more_body": True},
            {"type": "http.request", "body": b" " * 40000, "more_body": False},
        ]
    )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/solve",
        "raw_path": b"/api/v1/solve",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1),
        "server": ("127.0.0.1", 18000),
        "root_path": "",
    }

    async def receive():
        return next(chunks)

    async def send(message):
        messages.append(message)

    asyncio.run(app(scope, receive, send))
    assert messages[0]["status"] == 422
    assert json.loads(messages[1]["body"])["error"]["code"] == "request_too_large"


def test_unknown_routes_and_wrong_http_method_have_structured_errors(client):
    for path, status in [("/api/absent", 404), ("/api/v1/solve", 405)]:
        response = client.get(path)
        assert response.status_code == status
        assert_safe_json(response)
        if status == 405:
            assert response.headers["allow"] == "POST"


def test_openapi_describes_discriminators_bounds_exact_values_and_error_models(client):
    schema = client.get("/api/openapi.json").json()
    schemas = schema["components"]["schemas"]
    request_schema = schema["paths"]["/api/v1/solve"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert request_schema["discriminator"]["propertyName"] == "method"
    assert set(request_schema["discriminator"]["mapping"]) == {
        "gaussian",
        "gauss_jordan",
        "jacobi",
        "gauss_seidel",
    }
    assert schemas["SystemInput"]["properties"]["a"]["maxItems"] == 12
    row_ref = schemas["SystemInput"]["properties"]["a"]["items"]["$ref"]
    assert schemas[row_ref.rsplit("/", 1)[-1]]["maxItems"] == 12
    assert schemas["RationalValue"]["properties"]["numerator"]["type"] == "string"
    assert schemas["RationalValue"]["properties"]["denominator"]["type"] == "string"
    for path in ("/api/v1/analyze", "/api/v1/solve"):
        assert any(
            p["name"] == "x-request-id" and p["in"] == "header"
            for p in schema["paths"][path]["post"]["parameters"]
        )
        for status in ("200", "422", "500"):
            assert "X-Request-ID" in schema["paths"][path]["post"]["responses"][status]["headers"]
        for status in ("422", "500"):
            assert schema["paths"][path]["post"]["responses"][status]["content"][
                "application/json"
            ]["schema"]["$ref"].endswith("/ErrorResponse")
    for item in schemas.values():
        if item.get("type") == "object":
            assert item["additionalProperties"] is False


def test_openapi_export_matches_runtime_and_detects_stale_artifacts(client, tmp_path):
    output = tmp_path / "openapi.json"
    assert export_openapi(output)
    assert json.loads(output.read_text(encoding="utf-8")) == client.get("/api/openapi.json").json()
    assert export_openapi(output, check=True)
    output.write_text("{}", encoding="utf-8")
    assert not export_openapi(output, check=True)
    assert export_openapi(ROOT / "docs" / "openapi.json", check=True)


def test_export_script_is_cwd_independent_and_check_mode_fails_without_mutation(tmp_path):
    output = tmp_path / "schema.json"
    command = [sys.executable, str(ROOT / "scripts" / "export_openapi.py"), "--output", str(output)]
    subprocess.run(command, cwd=tmp_path, check=True, capture_output=True)
    output.write_text("{}", encoding="utf-8")
    result = subprocess.run([*command, "--check"], cwd=tmp_path, capture_output=True)
    assert result.returncode == 1
    assert output.read_text() == "{}"
