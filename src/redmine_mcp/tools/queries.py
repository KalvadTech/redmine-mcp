from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_queries(
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List saved queries visible to the current user. Use a query's
        id with list_issues(query_id=...) to apply it (Redmine accepts
        query_id as a filter on /issues.json)."""
        return await client().paginate("/queries.json", "queries", limit=limit, offset=offset)
