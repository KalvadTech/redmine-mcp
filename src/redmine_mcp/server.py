from __future__ import annotations

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette

from .middleware import RedmineAuthMiddleware, load_base_url
from .tools import register_all


def build_mcp() -> FastMCP:
    mcp = FastMCP("redmine")
    register_all(mcp)
    return mcp


def build_app(transport: httpx.AsyncBaseTransport | None = None) -> Starlette:
    """Return the ASGI app: FastMCP's Streamable HTTP app wrapped with the
    RedmineAuthMiddleware. The Redmine base URL is read once from the
    REDMINE_URL env var; missing or malformed values raise on boot.

    `transport` is for tests (respx). Production leaves it None so httpx uses
    its default.
    """
    base_url = load_base_url()
    mcp = build_mcp()
    app: Starlette = mcp.streamable_http_app()
    app.add_middleware(RedmineAuthMiddleware, base_url=base_url, transport=transport)
    return app
