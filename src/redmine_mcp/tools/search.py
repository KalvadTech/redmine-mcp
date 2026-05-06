from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def search(
        q: str,
        scope: str | None = None,
        all_words: bool | None = None,
        titles_only: bool | None = None,
        issues: bool | None = None,
        news: bool | None = None,
        documents: bool | None = None,
        changesets: bool | None = None,
        wiki_pages: bool | None = None,
        messages: bool | None = None,
        projects: bool | None = None,
        attachments: str | None = None,
        open_issues: bool | None = None,
        project_id: int | str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Full-text search across Redmine.

        scope: 'all', 'my_project', 'subprojects'. attachments: 'only', '1',
        '0'. Booleans become 1/0. project_id constrains the search.
        """
        params: dict[str, Any] = {"q": q, "scope": scope, "project_id": project_id}
        for key, value in {
            "all_words": all_words,
            "titles_only": titles_only,
            "issues": issues,
            "news": news,
            "documents": documents,
            "changesets": changesets,
            "wiki_pages": wiki_pages,
            "messages": messages,
            "projects": projects,
            "open_issues": open_issues,
        }.items():
            if value is not None:
                params[key] = 1 if value else 0
        if attachments is not None:
            params["attachments"] = attachments
        return await client().paginate(
            "/search.json", "results", params=params, limit=limit, offset=offset
        )
