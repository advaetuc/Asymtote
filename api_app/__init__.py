"""HTTP application composition; numerical algorithms belong in solver_core."""

from typing import Annotated

from fastapi import FastAPI, Header, Request

from api_app import services
from api_app.errors import install_error_handlers
from api_app.observability import RequestMiddleware, configure_logging, context
from api_models.health import HealthResponse
from api_models.requests import AnalyzeRequest, SolveRequest
from api_models.responses import AnalyzeOutcome, ErrorResponse, SolveOutcome

type CorrelationHeader = Annotated[
    str | None,
    Header(
        description="Optional correlation ID (1–64 ASCII letters, digits, '-' or '_'). "
        "Invalid values are replaced; the final ID is returned in X-Request-ID."
    ),
]

CORRELATION_RESPONSE_HEADERS = {
    "X-Request-ID": {"description": "Request correlation ID.", "schema": {"type": "string"}},
}


def create_app() -> FastAPI:
    """Create an independent stateless application instance."""
    app = FastAPI(
        title="TULYA API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    configure_logging()
    install_error_handlers(app)
    app.add_middleware(RequestMiddleware)

    errors: dict[int | str, dict[str, object]] = {
        200: {"headers": CORRELATION_RESPONSE_HEADERS},
        422: {
            "model": ErrorResponse,
            "description": "Invalid input or resource-policy violation.",
            "headers": CORRELATION_RESPONSE_HEADERS,
        },
        500: {
            "model": ErrorResponse,
            "description": "Unexpected internal error with correlation ID.",
            "headers": CORRELATION_RESPONSE_HEADERS,
        },
    }

    @app.get(
        "/api/health",
        response_model=HealthResponse,
        tags=["health"],
        operation_id="health",
        responses=errors,
    )
    def health(x_request_id: CorrelationHeader = None) -> HealthResponse:
        """Report process health without claiming solver readiness."""
        return HealthResponse(status="ok", api_version="0.1.0")

    @app.post(
        "/api/v1/analyze",
        response_model=AnalyzeOutcome,
        responses=errors,
        tags=["solver"],
        operation_id="analyze_system",
    )
    def analyze_system(
        payload: AnalyzeRequest, request: Request, x_request_id: CorrelationHeader = None
    ) -> AnalyzeOutcome:
        """Classify a system and explain conditional eligibility for all four methods."""
        return services.analyze(payload, context(request))

    @app.post(
        "/api/v1/solve",
        response_model=SolveOutcome,
        responses=errors,
        tags=["solver"],
        operation_id="solve_system",
    )
    def solve_system(
        payload: SolveRequest, request: Request, x_request_id: CorrelationHeader = None
    ) -> SolveOutcome:
        """Return full results, including mathematical non-success outcomes at HTTP 200."""
        return services.solve(payload, context(request))

    return app
