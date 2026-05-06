from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_users(
        name: str | None = None,
        status: int | None = None,
        group_id: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List users (admin only on most instances).

        status: 1=active, 2=registered, 3=locked. name matches login/firstname/
        lastname/email.
        """
        params = {"name": name, "status": status, "group_id": group_id}
        return await client().paginate(
            "/users.json", "users", params=params, limit=limit, offset=offset
        )

    @mcp.tool()
    async def get_user(id_or_current: int | str) -> dict[str, Any]:
        """Get a user by id, or pass the literal string 'current' for the
        authenticated user."""
        data = await client().get_json(f"/users/{id_or_current}.json")
        return data.get("user", data)
