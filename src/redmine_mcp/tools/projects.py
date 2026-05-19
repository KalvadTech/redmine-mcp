from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client, csv


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_projects(
        limit: int | None = None,
        offset: int = 0,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """List projects visible to the current user.

        include may contain: trackers, issue_categories, enabled_modules,
        time_entry_activities, issue_custom_fields.
        """
        params = {"include": csv(include)}
        return await client().paginate(
            "/projects.json", "projects", params=params, limit=limit, offset=offset
        )

    @mcp.tool()
    async def get_project(
        id: int | str,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get a single project by id or identifier.

        include may contain: trackers, issue_categories, enabled_modules,
        time_entry_activities, issue_custom_fields.
        """
        params = {"include": csv(include)}
        data = await client().get_json(f"/projects/{id}.json", params=params)
        return data.get("project", data)
