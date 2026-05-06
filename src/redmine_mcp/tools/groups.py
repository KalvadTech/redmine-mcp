from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client, csv


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_groups() -> dict[str, Any]:
        """List all groups (admin only)."""
        data = await client().get_json("/groups.json")
        return {"items": data.get("groups", [])}

    @mcp.tool()
    async def get_group(id: int, include: list[str] | None = None) -> dict[str, Any]:
        """Get a group by id. include may contain: users, memberships."""
        params = {"include": csv(include)}
        data = await client().get_json(f"/groups/{id}.json", params=params)
        return data.get("group", data)

    @mcp.tool()
    async def create_group(name: str, user_ids: list[int] | None = None) -> dict[str, Any]:
        """Create a group (admin only). user_ids seeds the group's members."""
        body: dict[str, Any] = {"name": name}
        if user_ids is not None:
            body["user_ids"] = user_ids
        data = await client().post_json("/groups.json", json={"group": body})
        return data.get("group", data)

    @mcp.tool()
    async def update_group(id: int, name: str) -> dict[str, Any]:
        """Rename a group."""
        await client().put_json(f"/groups/{id}.json", json={"group": {"name": name}})
        return {"id": id, "updated": True}

    @mcp.tool()
    async def delete_group(id: int) -> dict[str, Any]:
        """Delete a group."""
        await client().delete(f"/groups/{id}.json")
        return {"id": id, "deleted": True}

    @mcp.tool()
    async def add_user_to_group(group_id: int, user_id: int) -> dict[str, Any]:
        """Add a user to a group."""
        await client().post_json(
            f"/groups/{group_id}/users.json",
            json={"user_id": user_id},
        )
        return {"group_id": group_id, "user_id": user_id, "added": True}

    @mcp.tool()
    async def remove_user_from_group(group_id: int, user_id: int) -> dict[str, Any]:
        """Remove a user from a group."""
        await client().delete(f"/groups/{group_id}/users/{user_id}.json")
        return {"group_id": group_id, "user_id": user_id, "removed": True}
