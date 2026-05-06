from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_issue_statuses() -> dict[str, Any]:
        """List all issue statuses defined in the Redmine instance."""
        data = await client().get_json("/issue_statuses.json")
        return {"items": data.get("issue_statuses", [])}

    @mcp.tool()
    async def list_trackers() -> dict[str, Any]:
        """List all trackers (issue types) defined in the Redmine instance."""
        data = await client().get_json("/trackers.json")
        return {"items": data.get("trackers", [])}

    @mcp.tool()
    async def list_issue_categories(project_id: int | str) -> dict[str, Any]:
        """List issue categories for a project (id or identifier)."""
        data = await client().get_json(f"/projects/{project_id}/issue_categories.json")
        return {"items": data.get("issue_categories", [])}

    @mcp.tool()
    async def list_custom_fields() -> dict[str, Any]:
        """List custom fields. Requires admin privileges; returns 403 otherwise."""
        data = await client().get_json("/custom_fields.json")
        return {"items": data.get("custom_fields", [])}
