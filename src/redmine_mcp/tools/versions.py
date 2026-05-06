from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_versions(project_id: int | str) -> dict[str, Any]:
        """List versions for a project."""
        data = await client().get_json(f"/projects/{project_id}/versions.json")
        return {"items": data.get("versions", []), "total_count": data.get("total_count", 0)}

    @mcp.tool()
    async def get_version(id: int) -> dict[str, Any]:
        """Get a version by id."""
        data = await client().get_json(f"/versions/{id}.json")
        return data.get("version", data)

    @mcp.tool()
    async def create_version(
        project_id: int | str,
        name: str,
        status: str | None = None,
        sharing: str | None = None,
        due_date: str | None = None,
        description: str | None = None,
        wiki_page_title: str | None = None,
    ) -> dict[str, Any]:
        """Create a project version.

        status: open, locked, closed. sharing: none, descendants, hierarchy,
        tree, system. due_date is YYYY-MM-DD.
        """
        body: dict[str, Any] = {"name": name}
        for key, value in {
            "status": status,
            "sharing": sharing,
            "due_date": due_date,
            "description": description,
            "wiki_page_title": wiki_page_title,
        }.items():
            if value is not None:
                body[key] = value
        data = await client().post_json(
            f"/projects/{project_id}/versions.json",
            json={"version": body},
        )
        return data.get("version", data)

    @mcp.tool()
    async def update_version(
        id: int,
        name: str | None = None,
        status: str | None = None,
        sharing: str | None = None,
        due_date: str | None = None,
        description: str | None = None,
        wiki_page_title: str | None = None,
    ) -> dict[str, Any]:
        """Update a version."""
        body: dict[str, Any] = {}
        for key, value in {
            "name": name,
            "status": status,
            "sharing": sharing,
            "due_date": due_date,
            "description": description,
            "wiki_page_title": wiki_page_title,
        }.items():
            if value is not None:
                body[key] = value
        await client().put_json(f"/versions/{id}.json", json={"version": body})
        return {"id": id, "updated": True}

    @mcp.tool()
    async def delete_version(id: int) -> dict[str, Any]:
        """Delete a version."""
        await client().delete(f"/versions/{id}.json")
        return {"id": id, "deleted": True}
