from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client, csv


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_issues(
        project_id: int | str | None = None,
        status_id: str | None = None,
        assigned_to_id: int | str | None = None,
        tracker_id: int | None = None,
        category_id: int | None = None,
        query: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """List issues with optional filters.

        status_id accepts an id, 'open', 'closed', or '*'. assigned_to_id
        accepts an id or 'me'. include may contain: attachments, relations.
        """
        params = {
            "project_id": project_id,
            "status_id": status_id,
            "assigned_to_id": assigned_to_id,
            "tracker_id": tracker_id,
            "category_id": category_id,
            "subject": query,
            "sort": sort,
            "include": csv(include),
        }
        return await client().paginate(
            "/issues.json", "issues", params=params, limit=limit, offset=offset
        )

    @mcp.tool()
    async def get_issue(
        id: int,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get a single issue by id.

        include may contain: children, attachments, relations, changesets,
        journals, watchers, allowed_statuses.
        """
        params = {"include": csv(include)}
        data = await client().get_json(f"/issues/{id}.json", params=params)
        return data.get("issue", data)

    @mcp.tool()
    async def create_issue(
        project_id: int | str,
        subject: str,
        description: str | None = None,
        tracker_id: int | None = None,
        status_id: int | None = None,
        priority_id: int | None = None,
        assigned_to_id: int | None = None,
        category_id: int | None = None,
        parent_issue_id: int | None = None,
        watcher_user_ids: list[int] | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
        uploads: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create an issue.

        custom_fields entries: {"id": int, "value": str | list[str]}.
        uploads entries: {"token": str, "filename": str, "content_type": str,
        "description": str?}. Get a token via upload_attachment first.
        """
        body = _issue_body(
            project_id=project_id,
            subject=subject,
            description=description,
            tracker_id=tracker_id,
            status_id=status_id,
            priority_id=priority_id,
            assigned_to_id=assigned_to_id,
            category_id=category_id,
            parent_issue_id=parent_issue_id,
            watcher_user_ids=watcher_user_ids,
            custom_fields=custom_fields,
            uploads=uploads,
        )
        data = await client().post_json("/issues.json", json={"issue": body})
        return data.get("issue", data)

    @mcp.tool()
    async def update_issue(
        id: int,
        subject: str | None = None,
        description: str | None = None,
        project_id: int | str | None = None,
        tracker_id: int | None = None,
        status_id: int | None = None,
        priority_id: int | None = None,
        assigned_to_id: int | None = None,
        category_id: int | None = None,
        parent_issue_id: int | None = None,
        notes: str | None = None,
        private_notes: bool | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
        uploads: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update an issue. Pass notes to add a comment in the same call."""
        body = _issue_body(
            project_id=project_id,
            subject=subject,
            description=description,
            tracker_id=tracker_id,
            status_id=status_id,
            priority_id=priority_id,
            assigned_to_id=assigned_to_id,
            category_id=category_id,
            parent_issue_id=parent_issue_id,
            watcher_user_ids=None,
            custom_fields=custom_fields,
            uploads=uploads,
            notes=notes,
            private_notes=private_notes,
        )
        await client().put_json(f"/issues/{id}.json", json={"issue": body})
        return {"id": id, "updated": True}

    @mcp.tool()
    async def add_issue_note(
        id: int,
        notes: str,
        private: bool = False,
    ) -> dict[str, Any]:
        """Append a note (comment) to an issue."""
        body: dict[str, Any] = {"notes": notes, "private_notes": private}
        await client().put_json(f"/issues/{id}.json", json={"issue": body})
        return {"id": id, "noted": True}

    @mcp.tool()
    async def delete_issue(id: int) -> dict[str, Any]:
        """Delete an issue. Irreversible."""
        await client().delete(f"/issues/{id}.json")
        return {"id": id, "deleted": True}


def _issue_body(**fields: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in fields.items():
        if value is None:
            continue
        out[key] = value
    return out
