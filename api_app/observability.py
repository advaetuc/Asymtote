"""One privacy-preserving JSON log event and one correlation ID per HTTP request."""

import logging
import re
import time
from dataclasses import dataclass
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api_models.requests import Method
from api_models.responses import ErrorResponse, Issue
from solver_core.models import DomainModel

MAX_REQUEST_BODY_BYTES = 65_536
LOGGER = logging.getLogger("tulya.requests")
_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


@dataclass(slots=True)
class RequestContext:
    request_id: str
    method: Method | None = None
    equations: int | None = None
    unknowns: int | None = None
    result_status: str | None = None
    error_code: str | None = None
    warning_codes: tuple[str, ...] = ()
    exception_type: str | None = None


class RequestEvent(DomainModel):
    event: str = "http_request"
    request_id: str
    route: str
    http_method: str
    method: str | None
    equations: int | None
    unknowns: int | None
    duration_ms: float
    http_status: int
    result_status: str | None
    error_code: str | None
    warning_codes: tuple[str, ...]
    exception_type: str | None


def context(request: Request) -> RequestContext:
    value = request.scope["state"]["request_context"]
    if not isinstance(value, RequestContext):
        raise RuntimeError("Missing request context.")
    return value


def error_response(
    ctx: RequestContext, status: int, issue: Issue, *, details: tuple[Issue, ...] = ()
) -> Response:
    ctx.result_status, ctx.error_code = "error", issue.code
    body = ErrorResponse(request_id=ctx.request_id, error=issue, details=details)
    return Response(body.model_dump_json(), status_code=status, media_type="application/json")


def configure_logging() -> None:
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


class RequestMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        supplied = Request(scope).headers.get("x-request-id", "")
        ctx = RequestContext(supplied if _REQUEST_ID.fullmatch(supplied) else uuid4().hex)
        scope.setdefault("state", {})["request_context"] = ctx
        started, status, response_started = time.perf_counter(), 500, False

        async def send_with_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                status, response_started = message["status"], True
                headers = [
                    (k, v) for k, v in message.get("headers", []) if k.lower() != b"x-request-id"
                ]
                message = {
                    **message,
                    "headers": [*headers, (b"x-request-id", ctx.request_id.encode("ascii"))],
                }
            await send(message)

        try:
            # Bound bytes before JSON decoding, including chunked bodies with no length header.
            body = bytearray()
            body_received = False
            if scope["method"] in ("POST", "PUT", "PATCH"):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        ctx.result_status, status = "client_disconnected", 499
                        return
                    chunk = message.get("body", b"")
                    if len(body) + len(chunk) > MAX_REQUEST_BODY_BYTES:
                        response = error_response(
                            ctx,
                            422,
                            Issue(
                                code="request_too_large",
                                message="Request body exceeds 65536 bytes.",
                            ),
                        )
                        await response(scope, receive, send_with_id)
                        return
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        body_received = True
                        break
            delivered = False

            async def bounded_receive() -> Message:
                nonlocal delivered
                if body_received and not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, bounded_receive, send_with_id)
        except Exception as exc:
            ctx.exception_type = type(exc).__name__
            ctx.error_code, ctx.result_status = "internal_error", "error"
            if response_started:
                raise
            response = error_response(
                ctx,
                500,
                Issue(
                    code="internal_error",
                    message="An unexpected error occurred. Please retry using the request ID.",
                ),
            )
            await response(scope, receive, send_with_id)
        finally:
            route = getattr(scope.get("route"), "path", None)
            if route is None:
                # Known framework endpoints and early body rejections have no route object.
                known_routes = {
                    "/api/health",
                    "/api/v1/analyze",
                    "/api/v1/solve",
                    "/api/docs",
                    "/api/openapi.json",
                }
                route = scope["path"] if scope["path"] in known_routes else "<unmatched>"
            event = RequestEvent(
                request_id=ctx.request_id,
                route=route,
                http_method=scope["method"],
                method=ctx.method,
                equations=ctx.equations,
                unknowns=ctx.unknowns,
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
                http_status=status,
                result_status=ctx.result_status or ("ok" if status < 400 else "error"),
                error_code=ctx.error_code,
                warning_codes=ctx.warning_codes,
                exception_type=ctx.exception_type,
            )
            LOGGER.info(event.model_dump_json())
