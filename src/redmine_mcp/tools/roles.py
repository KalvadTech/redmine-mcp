from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_roles() -> dict[str, Any]:
        """List all roles."""
        data = await client().get_json("/roles.json")
        return {"items": data.get("roles", [])}

    @mcp.tool()
    async def get_role(id: int) -> dict[str, Any]:
        """Get a role by id, including its permissions list."""
        data = await client().get_json(f"/roles/{id}.json")
        return data.get("role", data)
