from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_time_entries(
        user_id: int | str | None = None,
        project_id: int | str | None = None,
        issue_id: int | None = None,
        spent_on_from: str | None = None,
        spent_on_to: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List time entries.

        spent_on_from / spent_on_to are YYYY-MM-DD strings. user_id accepts
        an id or 'me'.
        """
        params: dict[str, Any] = {
            "user_id": user_id,
            "project_id": project_id,
            "issue_id": issue_id,
        }
        if spent_on_from and spent_on_to:
            params["spent_on"] = f"><{spent_on_from}|{spent_on_to}"
        elif spent_on_from:
            params["spent_on"] = f">={spent_on_from}"
        elif spent_on_to:
            params["spent_on"] = f"<={spent_on_to}"
        return await client().paginate(
            "/time_entries.json",
            "time_entries",
            params=params,
            limit=limit,
            offset=offset,
        )

    @mcp.tool()
    async def create_time_entry(
        hours: float,
        activity_id: int,
        issue_id: int | None = None,
        project_id: int | str | None = None,
        spent_on: str | None = None,
        comments: str | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Log time on an issue or project. Provide exactly one of issue_id
        or project_id. spent_on is YYYY-MM-DD; defaults to today on Redmine."""
        if (issue_id is None) == (project_id is None):
            raise ValueError("provide exactly one of issue_id or project_id")
        body: dict[str, Any] = {
            "hours": hours,
            "activity_id": activity_id,
        }
        if issue_id is not None:
            body["issue_id"] = issue_id
        if project_id is not None:
            body["project_id"] = project_id
        if spent_on is not None:
            body["spent_on"] = spent_on
        if comments is not None:
            body["comments"] = comments
        if custom_fields is not None:
            body["custom_fields"] = custom_fields
        data = await client().post_json("/time_entries.json", json={"time_entry": body})
        return data.get("time_entry", data)

    @mcp.tool()
    async def update_time_entry(
        id: int,
        hours: float | None = None,
        activity_id: int | None = None,
        spent_on: str | None = None,
        comments: str | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update a time entry."""
        body: dict[str, Any] = {}
        if hours is not None:
            body["hours"] = hours
        if activity_id is not None:
            body["activity_id"] = activity_id
        if spent_on is not None:
            body["spent_on"] = spent_on
        if comments is not None:
            body["comments"] = comments
        if custom_fields is not None:
            body["custom_fields"] = custom_fields
        await client().put_json(f"/time_entries/{id}.json", json={"time_entry": body})
        return {"id": id, "updated": True}

    @mcp.tool()
    async def delete_time_entry(id: int) -> dict[str, Any]:
        """Delete a time entry."""
        await client().delete(f"/time_entries/{id}.json")
        return {"id": id, "deleted": True}
