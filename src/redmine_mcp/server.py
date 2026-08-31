from __future__ import annotations

import os

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from .discovery import McpEraCompatMiddleware, favicon_ico, favicon_png, server_card
from .middleware import RedmineAuthMiddleware, load_base_url
from .resources import register as register_resources
from .tools import register_all


def build_mcp(base_url: str) -> MCPServer:
    mcp = MCPServer("redmine")
    register_all(mcp)
    register_resources(mcp, base_url)
    return mcp


def _load_transport_security() -> TransportSecuritySettings | None:
    """Build the DNS-rebinding protection settings from MCP_ALLOWED_HOSTS.

    - empty (default): leave None, the server applies its localhost-only
      defaults (right for local dev).
    - comma list of hostnames: enable protection with that allowlist.
      Each bare entry also matches the same host with any port.
    - '*': disable DNS-rebinding protection entirely (right when behind
      a trusted reverse proxy that already enforces hostnames).
    """
    raw = os.environ.get("MCP_ALLOWED_HOSTS", "").strip()
    if not raw:
        return None
    if raw == "*":
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    hosts: list[str] = []
    for entry in raw.split(","):
        host = entry.strip()
        if not host:
            continue
        hosts.append(host)
        if ":" not in host:
            hosts.append(f"{host}:*")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
    )


async def _up(request: Request) -> PlainTextResponse:
    del request
    return PlainTextResponse("ok")


def build_app(transport: httpx.AsyncBaseTransport | None = None) -> Starlette:
    """Return the ASGI app: the Streamable HTTP app wrapped with the
    McpEraCompatMiddleware (header normalization) and RedmineAuthMiddleware
    (outermost, per-request auth). Public metadata routes (server card,
    favicons, /up) bypass auth. The Redmine base URL is read once from the
    REDMINE_URL env var; missing or malformed values raise on boot.

    `transport` is for tests (respx). Production leaves it None so httpx uses
    its default.
    """
    base_url = load_base_url()
    mcp = build_mcp(base_url)
    app: Starlette = mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=_load_transport_security(),
    )
    app.routes.append(Route("/up", _up, methods=["GET"]))
    app.routes.append(Route("/.well-known/mcp/server-card/mcp", server_card, methods=["GET"]))
    app.routes.append(Route("/favicon.ico", favicon_ico, methods=["GET"]))
    app.routes.append(Route("/favicon.png", favicon_png, methods=["GET"]))
    # Starlette wraps in reverse order of add_middleware: RedmineAuthMiddleware
    # stays outermost, McpEraCompatMiddleware runs just in front of the app.
    app.add_middleware(McpEraCompatMiddleware)
    app.add_middleware(RedmineAuthMiddleware, base_url=base_url, transport=transport)
    return app
