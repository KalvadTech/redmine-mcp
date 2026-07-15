from __future__ import annotations

import re
from urllib.parse import urlsplit

from mcp.server.fastmcp import FastMCP

from ..client import get_redmine_client
from ..resources import format_issue, format_project

_IssuePattern = re.compile(r"^/issues/(\d+)$")
_ProjectPattern = re.compile(r"^/projects/([^/]+)$")


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def open_redmine_url(url: str) -> str:
        """Open a Redmine URL and return the entity as Markdown.

        Use this when the user pastes a Redmine link (e.g.
        https://pm.kalvad.cloud/issues/4085) and the automatic resource
        template was not used by the client.
        """
        client = get_redmine_client()
        base_url = client.base_url
        parsed = urlsplit(url)
        base_parsed = urlsplit(base_url)

        if parsed.scheme != base_parsed.scheme:
            return _wrong_instance(base_url, url)
        if parsed.netloc != base_parsed.netloc:
            return _wrong_instance(base_url, url)

        base_path = base_parsed.path.rstrip("/")
        if not parsed.path.startswith(base_path):
            return _wrong_instance(base_url, url)

        relative = parsed.path[len(base_path) :]

        if match := _IssuePattern.match(relative):
            data = await client.get_json(f"/issues/{match.group(1)}.json")
            return format_issue(data.get("issue", data))

        if match := _ProjectPattern.match(relative):
            data = await client.get_json(f"/projects/{match.group(1)}.json")
            return format_project(data.get("project", data))

        return (
            f"Unsupported Redmine URL: {url}\n\n"
            f"Currently supported: {base_url}/issues/<id> and {base_url}/projects/<identifier>."
        )


def _wrong_instance(base_url: str, url: str) -> str:
    return f"The URL {url} does not belong to the configured Redmine instance ({base_url})."
