"""Public discovery surface: MCP Server Card, favicons, and the era-compat shim.

Everything here is reachable without credentials (see `_PUBLIC_PATHS` in
middleware.py) and carries only public metadata.
"""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from . import __version__

MCP_PATH = "/mcp"

# Legacy (handshake-based) revisions the SDK's legacy transport negotiates, and
# the modern (stateless) revision. Keep in sync with mcp_types.version
# (HANDSHAKE_PROTOCOL_VERSIONS / MODERN_PROTOCOL_VERSIONS of the pinned SDK).
LEGACY_PROTOCOL_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25")
MODERN_PROTOCOL_VERSIONS = ("2026-07-28",)
_LATEST_LEGACY_VERSION = LEGACY_PROTOCOL_VERSIONS[-1]

_PROTOCOL_HEADER = b"mcp-protocol-version"
_METHOD_HEADER = b"mcp-method"
_NAME_HEADER = b"mcp-name"
_ENVELOPE_PREFIX = "io.modelcontextprotocol/"

# Methods that only exist in legacy revisions: 2026-07-28 removed them, so they
# must always be routed to the legacy transport regardless of the header.
_LEGACY_ONLY_METHODS = {"initialize", "notifications/initialized", "ping"}

# Methods whose params address a named item, mirrored into the Mcp-Name header
# on the modern transport (SEP-2243).
_NAMED_METHODS = {
    "tools/call": "name",
    "prompts/get": "name",
    "resources/read": "uri",
    "resources/templates/read": "uri",
}

_CARD_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type, If-None-Match",
    "Access-Control-Expose-Headers": "ETag",
    "Cache-Control": "public, max-age=3600",
}

_FAVICON_HEADERS = {"Cache-Control": "public, max-age=86400"}


def _server_card(origin: str) -> dict[str, Any]:
    """Build the Server Card (SEP-2127). `origin` is the request's base URL,
    so the card is correct behind a reverse proxy (uvicorn proxy_headers)."""
    origin = origin.rstrip("/")
    return {
        "$schema": "https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json",
        "name": "com.github.kalvadtech/redmine-mcp",
        "title": "Redmine MCP",
        "version": __version__,
        "description": (
            "Stateless MCP server for Redmine. Each request carries the user's own "
            "Redmine API key; no database, no shared secret."
        ),
        "websiteUrl": "https://github.com/KalvadTech/redmine-mcp",
        "icons": [
            {"src": f"{origin}/favicon.png", "mimeType": "image/png", "sizes": ["32x32"]},
        ],
        "remotes": [
            {
                "type": "streamable-http",
                "url": f"{origin}{MCP_PATH}",
                "supportedProtocolVersions": [
                    *LEGACY_PROTOCOL_VERSIONS,
                    *MODERN_PROTOCOL_VERSIONS,
                ],
                "headers": [
                    {
                        "name": "Authorization",
                        "description": "Bearer token holding the user's Redmine API key.",
                        "isRequired": True,
                        "isSecret": True,
                        "value": "Bearer {token}",
                        "variables": {
                            "token": {
                                "description": "Redmine API key (Account page -> API access key).",
                                "isRequired": True,
                                "isSecret": True,
                            }
                        },
                    }
                ],
            }
        ],
    }


async def server_card(request: Request) -> Response:
    body = json.dumps(_server_card(str(request.base_url))).encode("utf-8")
    etag = hashlib.sha256(body).hexdigest()
    headers = {**_CARD_HEADERS, "ETag": f'"{etag}"'}
    if request.headers.get("if-none-match") == f'"{etag}"':
        return Response(status_code=304, headers=headers)
    return Response(body, media_type="application/mcp-server-card+json", headers=headers)


async def favicon_ico(request: Request) -> Response:
    del request
    data = files("redmine_mcp").joinpath("static/favicon.ico").read_bytes()
    return Response(data, media_type="image/x-icon", headers=_FAVICON_HEADERS)


async def favicon_png(request: Request) -> Response:
    del request
    data = files("redmine_mcp").joinpath("static/favicon.png").read_bytes()
    return Response(data, media_type="image/png", headers=_FAVICON_HEADERS)


def _set_header(
    headers: list[tuple[bytes, bytes]], name: bytes, value: bytes
) -> list[tuple[bytes, bytes]]:
    return [(k, v) for k, v in headers if k != name] + [(name, value)]


def _has_header(headers: list[tuple[bytes, bytes]], name: bytes) -> bool:
    return any(k == name for k, _ in headers)


def _compat_headers(
    headers: list[tuple[bytes, bytes]], body: bytes
) -> list[tuple[bytes, bytes]]:
    """Rewrite routing headers so the SDK's era router accepts the request.

    The SDK routes on `MCP-Protocol-Version` alone and the modern handler then
    requires the mirrored `Mcp-Method`/`Mcp-Name` headers and rejects legacy
    message shapes with 400. Dual-era clients (e.g. Mistral Le Chat) send
    mixed shapes, so normalize here; the body is never modified.
    """
    try:
        message = json.loads(body)
    except ValueError:
        return headers
    if not isinstance(message, dict):
        return headers
    method = message.get("method")
    if not isinstance(method, str):
        return headers
    params = message.get("params")
    params = params if isinstance(params, dict) else {}
    meta = params.get("_meta")
    has_envelope = isinstance(meta, dict) and any(
        isinstance(k, str) and k.startswith(_ENVELOPE_PREFIX) for k in meta
    )
    pv = next((v.decode("latin-1") for k, v in headers if k == _PROTOCOL_HEADER), None)

    if method in _LEGACY_ONLY_METHODS:
        requested = params.get("protocolVersion")
        version = (
            requested
            if isinstance(requested, str) and requested in LEGACY_PROTOCOL_VERSIONS
            else _LATEST_LEGACY_VERSION
        )
        return _set_header(headers, _PROTOCOL_HEADER, version.encode("latin-1"))

    if not has_envelope and (pv is None or pv in LEGACY_PROTOCOL_VERSIONS):
        return headers

    if pv is None:
        envelope_version = (
            meta.get(f"{_ENVELOPE_PREFIX}protocolVersion") if isinstance(meta, dict) else None
        )
        if isinstance(envelope_version, str):
            headers = _set_header(headers, _PROTOCOL_HEADER, envelope_version.encode("latin-1"))
    if not _has_header(headers, _METHOD_HEADER):
        headers = _set_header(headers, _METHOD_HEADER, method.encode("latin-1"))
    name_param = _NAMED_METHODS.get(method)
    if name_param is not None and not _has_header(headers, _NAME_HEADER):
        value = params.get(name_param)
        if isinstance(value, str):
            headers = _set_header(headers, _NAME_HEADER, value.encode("latin-1"))
    return headers


class McpEraCompatMiddleware:
    """Pure-ASGI shim in front of the Streamable HTTP app. For POSTs to the
    MCP endpoint it buffers the (small) JSON-RPC body, replays it downstream,
    and normalizes the era-routing headers via `_compat_headers`."""

    def __init__(self, app: Any) -> None:
        self._app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if (
            scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != MCP_PATH
        ):
            await self._app(scope, receive, send)
            return

        body = b""
        while True:
            message: dict[str, Any] = await receive()
            if message["type"] != "http.request":
                break
            body += message.get("body", b"")
            if not message.get("more_body"):
                break

        scope = {**scope, "headers": _compat_headers(scope.get("headers", []), body)}
        replayed = False

        async def replay_receive() -> dict[str, Any]:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            reply: dict[str, Any] = await receive()
            return reply

        await self._app(scope, replay_receive, send)
