from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlsplit

import httpx

from .client import RedmineClient, reset_current_client, set_current_client
from .errors import AuthHeaderError

_HEADER_KEY = b"x-redmine-api-key"
_MIN_KEY_LEN = 16
_MAX_KEY_LEN = 128

_HEALTH_PATHS = {"/", "/healthz", "/health"}


class RedmineAuthMiddleware:
    """Pure-ASGI middleware: extracts the user's API key from
    X-Redmine-API-Key, builds a per-request RedmineClient against the
    server-configured base URL, binds it to a ContextVar, and tears it down
    only after the response (including SSE streams) is fully sent.

    BaseHTTPMiddleware can't be used here because FastMCP's Streamable HTTP
    responses are SSE streams; that middleware closes the client in finally
    before the tool ever runs.
    """

    def __init__(
        self,
        app: Any,
        *,
        base_url: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._app = app
        self._base_url = base_url
        self._transport = transport

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        if scope.get("path") in _HEALTH_PATHS:
            await self._app(scope, receive, send)
            return

        api_key_raw: str | None = None
        for name, value in scope.get("headers", []):
            if name == _HEADER_KEY:
                api_key_raw = value.decode("latin-1")
                break

        try:
            api_key = _extract_api_key(api_key_raw)
        except AuthHeaderError as exc:
            await _send_jsonrpc_error(send, exc)
            return

        client = RedmineClient(self._base_url, api_key, transport=self._transport)
        token = set_current_client(client)
        try:
            await self._app(scope, receive, send)
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
        raise AuthHeaderError("missing X-Redmine-API-Key header")
    raw = raw.strip()
    if not (_MIN_KEY_LEN <= len(raw) <= _MAX_KEY_LEN):
        raise AuthHeaderError(
            f"X-Redmine-API-Key length must be between {_MIN_KEY_LEN} and {_MAX_KEY_LEN}"
        )
    if any(c.isspace() for c in raw):
        raise AuthHeaderError("X-Redmine-API-Key must not contain whitespace")
    return raw


async def _send_jsonrpc_error(send: Any, exc: AuthHeaderError) -> None:
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": exc.message},
            "id": None,
        }
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": exc.status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body, "more_body": False})
