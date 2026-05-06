from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_issue_relations(issue_id: int) -> dict[str, Any]:
        """List relations on an issue."""
        data = await client().get_json(f"/issues/{issue_id}/relations.json")
        return {"items": data.get("relations", [])}

    @mcp.tool()
    async def get_relation(id: int) -> dict[str, Any]:
        """Get a single issue relation by id."""
        data = await client().get_json(f"/relations/{id}.json")
        return data.get("relation", data)

    @mcp.tool()
    async def create_issue_relation(
        issue_id: int,
        issue_to_id: int,
        relation_type: str = "relates",
        delay: int | None = None,
    ) -> dict[str, Any]:
        """Create a relation between two issues.

        relation_type: relates, duplicates, duplicated, blocks, blocked,
        precedes, follows, copied_to, copied_from. delay applies only to
        precedes/follows (number of days).
        """
        body: dict[str, Any] = {
            "issue_to_id": issue_to_id,
            "relation_type": relation_type,
        }
        if delay is not None:
            body["delay"] = delay
        data = await client().post_json(
            f"/issues/{issue_id}/relations.json",
            json={"relation": body},
        )
        return data.get("relation", data)

    @mcp.tool()
    async def delete_relation(id: int) -> dict[str, Any]:
        """Delete an issue relation."""
        await client().delete(f"/relations/{id}.json")
        return {"id": id, "deleted": True}
