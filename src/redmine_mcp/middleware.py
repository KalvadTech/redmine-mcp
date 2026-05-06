from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .client import RedmineClient, reset_current_client, set_current_client
from .errors import AuthHeaderError

_HEADER_KEY = "X-Redmine-API-Key"
_MIN_KEY_LEN = 16
_MAX_KEY_LEN = 128

_HEALTH_PATHS = {"/", "/healthz", "/health"}


class RedmineAuthMiddleware(BaseHTTPMiddleware):
    """Extracts the user's API key from X-Redmine-API-Key, builds a per-request
    RedmineClient against the server-configured base URL, binds it to a
    ContextVar, and tears it down on exit. Credentials are never persisted.
    """

    def __init__(
        self,
        app: Callable[..., Awaitable[None]],
        *,
        base_url: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(app)
        self._base_url = base_url
        self._transport = transport

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in _HEALTH_PATHS:
            return await call_next(request)
        try:
            api_key = _extract_api_key(request.headers.get(_HEADER_KEY))
        except AuthHeaderError as exc:
            return _error_response(exc)

        client = RedmineClient(self._base_url, api_key, transport=self._transport)
        token = set_current_client(client)
        try:
            return await call_next(request)
        finally:
            reset_current_client(token)
            await client.aclose()


def load_base_url() -> str:
    """Read and validate REDMINE_URL at startup. Raises if missing or
    malformed so the server fails fast instead of failing per-request."""
    raw = os.environ.get("REDMINE_URL", "").strip()
    if not raw:
        raise RuntimeError("REDMINE_URL env var is required")
    parsed = urlsplit(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RuntimeError(
            f"REDMINE_URL must be an absolute http(s) URL, got: {raw!r}"
        )
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"


def _extract_api_key(raw: str | None) -> str:
    if not raw:
        raise AuthHeaderError(f"missing {_HEADER_KEY} header")
    raw = raw.strip()
    if not (_MIN_KEY_LEN <= len(raw) <= _MAX_KEY_LEN):
        raise AuthHeaderError(
            f"{_HEADER_KEY} length must be between {_MIN_KEY_LEN} and {_MAX_KEY_LEN}"
        )
    if any(c.isspace() for c in raw):
        raise AuthHeaderError(f"{_HEADER_KEY} must not contain whitespace")
    return raw


def _error_response(exc: AuthHeaderError) -> JSONResponse:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": exc.message},
            "id": None,
        },
        status_code=exc.status,
    )
