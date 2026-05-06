from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_news(
        project_id: int | str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List news entries. If project_id is None, lists across all
        projects; otherwise lists news for a single project. The Redmine
        API only exposes index for news (no get/create/update/delete)."""
        path = "/news.json" if project_id is None else f"/projects/{project_id}/news.json"
        return await client().paginate(path, "news", limit=limit, offset=offset)
