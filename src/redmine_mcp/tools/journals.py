from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def update_journal_note(
        id: int,
        notes: str,
        private_notes: bool | None = None,
    ) -> dict[str, Any]:
        """Edit an existing journal entry's note. Only the note text and
        its privacy can be changed; the journal's other fields are
        immutable. Use add_issue_note to add a new note instead."""
        body: dict[str, Any] = {"notes": notes}
        if private_notes is not None:
            body["private_notes"] = private_notes
        await client().put_json(f"/journals/{id}.json", json={"journal": body})
        return {"id": id, "updated": True}
