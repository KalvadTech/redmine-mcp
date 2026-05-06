from __future__ import annotations

from typing import Any
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_wiki_pages(project_id: int | str) -> dict[str, Any]:
        """List wiki pages in a project. Returns the full index in one call;
        Redmine does not paginate this endpoint."""
        data = await client().get_json(f"/projects/{project_id}/wiki/index.json")
        return {"items": data.get("wiki_pages", [])}

    @mcp.tool()
    async def get_wiki_page(
        project_id: int | str,
        title: str,
        version: int | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get a wiki page by title. version fetches a specific revision.
        include may contain: attachments."""
        path = f"/projects/{project_id}/wiki/{quote(title, safe='')}"
        if version is not None:
            path = f"{path}/{version}"
        params: dict[str, Any] = {}
        if include:
            params["include"] = ",".join(include)
        data = await client().get_json(f"{path}.json", params=params or None)
        return data.get("wiki_page", data)

    @mcp.tool()
    async def create_or_update_wiki_page(
        project_id: int | str,
        title: str,
        text: str,
        comments: str | None = None,
        parent_title: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Create or replace a wiki page (Redmine PUT is upsert).

        version is the expected current version for optimistic concurrency;
        if it does not match the server's, Redmine returns 409.
        """
        body: dict[str, Any] = {"text": text}
        if comments is not None:
            body["comments"] = comments
        if parent_title is not None:
            body["parent_title"] = parent_title
        if version is not None:
            body["version"] = version
        path = f"/projects/{project_id}/wiki/{quote(title, safe='')}.json"
        await client().put_json(path, json={"wiki_page": body})
        return {"project_id": project_id, "title": title, "saved": True}

    @mcp.tool()
    async def delete_wiki_page(project_id: int | str, title: str) -> dict[str, Any]:
        """Delete a wiki page by title."""
        path = f"/projects/{project_id}/wiki/{quote(title, safe='')}.json"
        await client().delete(path)
        return {"project_id": project_id, "title": title, "deleted": True}
