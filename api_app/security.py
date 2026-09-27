"""Browser origin checks and response headers, independent of the frontend proxy."""

from urllib.parse import urlsplit

from starlette.requests import Request

SECURITY_HEADERS = {
    b"x-content-type-options": b"nosniff",
    b"referrer-policy": b"no-referrer",
    b"x-frame-options": b"DENY",
    b"permissions-policy": b"camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    b"cache-control": b"no-store",
}
API_CSP = b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"


def cross_origin(request: Request) -> bool:
    """Fetch metadata cannot be set by page scripts; CLI clients need no Origin."""
    site = request.headers.get("sec-fetch-site")
    if site in {"cross-site", "same-site"}:
        return True
    origin = request.headers.get("origin")
    if origin is None:
        return False
    if site == "same-origin":
        return False  # Retains the browser's origin through the local Next.js rewrite.
    try:
        parsed = urlsplit(origin)
        if parsed.scheme not in {"http", "https"} or parsed.path or parsed.query or parsed.fragment:
            return True
        if parsed.username is not None or parsed.password is not None:
            return True
        # Host is preserved by Vercel; do not trust arbitrary forwarded-host headers.
        return (parsed.scheme, parsed.netloc.lower()) != (
            request.url.scheme,
            request.headers.get("host", "").lower(),
        )
    except ValueError:
        return True
