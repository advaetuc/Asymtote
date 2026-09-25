"""Phase 0 process-health and application-isolation checks."""

from fastapi.testclient import TestClient

from api.index import app
from api_app import create_app


def test_health_has_a_stable_public_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "api_version": "0.1.0"}
    assert response.headers["content-type"] == "application/json"
    assert "access-control-allow-origin" not in response.headers


def test_factory_instances_do_not_share_mutable_application_state() -> None:
    first = create_app()
    second = create_app()
    first.state.probe = "first-only"
    assert not hasattr(second.state, "probe")


def test_health_schema_is_exposed_under_the_api_prefix() -> None:
    with TestClient(app) as client:
        schema_response = client.get("/api/openapi.json")
    assert schema_response.status_code == 200
    schema = schema_response.json()
    assert "/api/health" in schema["paths"]
    assert schema["components"]["schemas"]["HealthResponse"]["additionalProperties"] is False
