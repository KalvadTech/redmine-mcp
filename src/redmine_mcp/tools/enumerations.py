from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_issue_priorities() -> dict[str, Any]:
        """List issue priority enumeration values."""
        data = await client().get_json("/enumerations/issue_priorities.json")
        return {"items": data.get("issue_priorities", [])}

    @mcp.tool()
    async def list_time_entry_activities() -> dict[str, Any]:
        """List time entry activity enumeration values."""
        data = await client().get_json("/enumerations/time_entry_activities.json")
        return {"items": data.get("time_entry_activities", [])}

    @mcp.tool()
    async def list_document_categories() -> dict[str, Any]:
        """List document category enumeration values."""
        data = await client().get_json("/enumerations/document_categories.json")
        return {"items": data.get("document_categories", [])}
