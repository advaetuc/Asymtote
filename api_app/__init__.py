"""HTTP application composition; numerical algorithms belong in solver_core."""

from fastapi import FastAPI

from api_models.health import HealthResponse


def create_app() -> FastAPI:
    """Create an independent stateless application instance."""
    app = FastAPI(
        title="TULYA API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        """Report process health without claiming solver readiness."""
        return HealthResponse(status="ok", api_version="0.1.0")

    return app
