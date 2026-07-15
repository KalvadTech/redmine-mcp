from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import get_redmine_client


def register(mcp: FastMCP, base_url: str) -> None:
    """Register Redmine URL resource templates for the configured base URL.

    When a user pastes a Redmine URL matching ``base_url``, the MCP client
    can read it through this server instead of fetching it from the web.
    """
    base = base_url.rstrip("/")

    @mcp.resource(
        f"{base}/issues/{{id}}",
        name="redmine-issue",
        title="Redmine issue",
        description="Fetch a Redmine issue by its URL.",
        mime_type="text/markdown",
    )
    async def redmine_issue(id: str) -> str:
        client = get_redmine_client()
        data = await client.get_json(f"/issues/{id}.json")
        return format_issue(data.get("issue", data))

    @mcp.resource(
        f"{base}/projects/{{identifier}}",
        name="redmine-project",
        title="Redmine project",
        description="Fetch a Redmine project by its URL.",
        mime_type="text/markdown",
    )
    async def redmine_project(identifier: str) -> str:
        client = get_redmine_client()
        data = await client.get_json(f"/projects/{identifier}.json")
        return format_project(data.get("project", data))


def format_issue(issue: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Issue #{issue.get('id')}: {issue.get('subject', '')}",
        "",
        f"**Project:** {_nested_name(issue.get('project'))}",
        f"**Tracker:** {_nested_name(issue.get('tracker'))}",
        f"**Status:** {_nested_name(issue.get('status'))}",
        f"**Priority:** {_nested_name(issue.get('priority'))}",
        f"**Author:** {_nested_name(issue.get('author'))}",
    ]
    if issue.get("assigned_to"):
        lines.append(f"**Assigned to:** {_nested_name(issue['assigned_to'])}")
    if issue.get("start_date"):
        lines.append(f"**Start date:** {issue['start_date']}")
    if issue.get("due_date"):
        lines.append(f"**Due date:** {issue['due_date']}")
    if issue.get("done_ratio") is not None:
        lines.append(f"**Done ratio:** {issue['done_ratio']}%")
    if issue.get("estimated_hours") is not None:
        lines.append(f"**Estimated hours:** {issue['estimated_hours']}")
    if issue.get("spent_hours") is not None:
        lines.append(f"**Spent hours:** {issue['spent_hours']}")
    if issue.get("created_on"):
        lines.append(f"**Created:** {issue['created_on']}")
    if issue.get("updated_on"):
        lines.append(f"**Updated:** {issue['updated_on']}")

    description = issue.get("description") or "*No description*"
    lines.extend(["", "## Description", "", description])
    return "\n".join(lines)


def format_project(project: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Project: {project.get('name', '')}",
        "",
        f"**Identifier:** {project.get('identifier', '')}",
        f"**Status:** {'active' if project.get('status') == 1 else 'closed'}",
    ]
    if project.get("created_on"):
        lines.append(f"**Created:** {project['created_on']}")
    if project.get("updated_on"):
        lines.append(f"**Updated:** {project['updated_on']}")

    description = project.get("description") or "*No description*"
    lines.extend(["", "## Description", "", description])
    return "\n".join(lines)


def _nested_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name", ""))
    return ""
