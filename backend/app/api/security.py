"""Security helpers: security headers, request-size limit, rate limit, admin token."""

from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

MAX_BODY_BYTES = 64 * 1024
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")

API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
# Policy for the web pages themselves when the API also serves the built frontend (single-domain hosting).
APP_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
    "connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)
DOCS_CSP = (
    "default-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; frame-ancestors 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
        response = await call_next(request)
        is_docs = request.url.path.startswith(DOCS_PATHS)
        is_api = request.url.path.startswith("/api")
        response.headers["Content-Security-Policy"] = DOCS_CSP if is_docs else API_CSP if is_api else APP_CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers.setdefault("Cache-Control", "no-store")
        return response


class RateLimiter:
    """Small in-memory sliding-window limiter, per client address. 0 disables it."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, request: Request) -> None:
        if self.per_minute <= 0:
            return
        who = request.client.host if request.client else "unknown"  # never trust X-Forwarded-For here
        now = time.monotonic()
        hits = self._hits[who]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= self.per_minute:
            raise HTTPException(status_code=429, detail="Too many requests. Try again in a minute.")
        hits.append(now)


def check_admin(request: Request) -> None:
    """If DAGSHIELD_ADMIN_TOKEN is set, mutating endpoints require it (constant-time compare)."""
    expected = request.app.state.settings.admin_token
    if not expected:
        return
    given = request.headers.get("x-admin-token", "")
    if not hmac.compare_digest(given.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Admin token required for this action.")
