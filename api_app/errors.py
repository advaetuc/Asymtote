"""Stable errors without raw request bodies, rejected values, or exception tracebacks."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import Response

from api_app.observability import context, error_response
from api_models.responses import Issue
from solver_core.errors import InputError, ResourceLimitError, SolverError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> Response:
        issues: list[Issue] = []
        for item in exc.errors()[:32]:
            cause = item.get("ctx", {}).get("error")
            issues.append(
                Issue(
                    code=cause.code.value if isinstance(cause, SolverError) else item["type"],
                    message=cause.message
                    if isinstance(cause, SolverError)
                    else "Invalid or missing request field.",
                    location=tuple(item["loc"]),
                )
            )
        return error_response(
            context(request),
            422,
            Issue(code="validation_error", message="Request validation failed."),
            details=tuple(issues),
        )

    async def domain_error(request: Request, exc: Exception) -> Response:
        if not isinstance(exc, (InputError, ResourceLimitError)):
            raise exc
        return error_response(
            context(request),
            422,
            Issue(code=exc.code.value, message=exc.message, location=exc.location),
        )

    app.add_exception_handler(InputError, domain_error)
    app.add_exception_handler(ResourceLimitError, domain_error)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> Response:
        response = error_response(
            context(request),
            exc.status_code,
            Issue(code=f"http_{exc.status_code}", message="The HTTP request could not be handled."),
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response
