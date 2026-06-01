from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_memberships(
        project_id: int | str,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List user/group memberships for a project."""
        return await client().paginate(
            f"/projects/{project_id}/memberships.json",
            "memberships",
            limit=limit,
            offset=offset,
        )

    @mcp.tool()
    async def get_membership(id: int) -> dict[str, Any]:
        """Get a single membership by id."""
        data = await client().get_json(f"/memberships/{id}.json")
        return data.get("membership", data)

    @mcp.tool()
    async def add_project_member(
        project_id: int | str,
        role_ids: list[int],
        user_id: int | None = None,
        group_id: int | None = None,
    ) -> dict[str, Any]:
        """Add a user or a group to a project with the given role ids.
        Provide exactly one of user_id or group_id."""
        if (user_id is None) == (group_id is None):
            raise ValueError("provide exactly one of user_id or group_id")
        body: dict[str, Any] = {"role_ids": role_ids}
        if user_id is not None:
            body["user_id"] = user_id
        else:
            body["group_id"] = group_id
        data = await client().post_json(
            f"/projects/{project_id}/memberships.json",
            json={"membership": body},
        )
        return data.get("membership", data)

    @mcp.tool()
    async def update_membership(id: int, role_ids: list[int]) -> dict[str, Any]:
        """Replace a membership's role ids."""
        await client().put_json(
            f"/memberships/{id}.json",
            json={"membership": {"role_ids": role_ids}},
        )
        return {"id": id, "updated": True}

    @mcp.tool()
    async def remove_membership(id: int) -> dict[str, Any]:
        """Remove a membership from its project."""
        await client().delete(f"/memberships/{id}.json")
        return {"id": id, "deleted": True}
