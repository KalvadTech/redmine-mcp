from __future__ import annotations

import httpx
import pytest
import respx
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel.helper_types import ReadResourceContents

from redmine_mcp.client import RedmineClient

BASE = "https://redmine.test"
KEY = "x" * 40


@respx.mock
async def test_resource_templates_listed(mcp: FastMCP) -> None:
    templates = await mcp.list_resource_templates()
    uris = {t.uriTemplate for t in templates}
    assert f"{BASE}/issues/{{id}}" in uris
    assert f"{BASE}/projects/{{identifier}}" in uris


@respx.mock
async def test_read_issue_resource(mcp: FastMCP, bound_client: RedmineClient) -> None:
    respx.get(f"{BASE}/issues/4085.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "issue": {
                    "id": 4085,
                    "subject": "Fix login",
                    "project": {"id": 1, "name": "Website"},
                    "tracker": {"id": 1, "name": "Bug"},
                    "status": {"id": 2, "name": "In Progress"},
                    "priority": {"id": 3, "name": "High"},
                    "author": {"id": 5, "name": "Alice"},
                    "assigned_to": {"id": 6, "name": "Bob"},
                    "description": "Users cannot log in.",
                    "done_ratio": 50,
                    "created_on": "2026-01-01T00:00:00Z",
                    "updated_on": "2026-01-02T00:00:00Z",
                }
            },
        )
    )

    result = await mcp.read_resource(f"{BASE}/issues/4085")
    contents = list(result)
    assert len(contents) == 1
    content = contents[0]
    assert isinstance(content, ReadResourceContents)
    assert content.mime_type == "text/markdown"
    text = content.content
    assert "Issue #4085: Fix login" in text
    assert "**Status:** In Progress" in text
    assert "**Assigned to:** Bob" in text
    assert "Users cannot log in." in text


@respx.mock
async def test_read_project_resource(mcp: FastMCP, bound_client: RedmineClient) -> None:
    respx.get(f"{BASE}/projects/website.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "project": {
                    "id": 1,
                    "name": "Website",
                    "identifier": "website",
                    "description": "Company website project.",
                    "status": 1,
                    "created_on": "2026-01-01T00:00:00Z",
                    "updated_on": "2026-01-02T00:00:00Z",
                }
            },
        )
    )

    result = await mcp.read_resource(f"{BASE}/projects/website")
    contents = list(result)
    assert len(contents) == 1
    content = contents[0]
    assert isinstance(content, ReadResourceContents)
    assert content.mime_type == "text/markdown"
    text = content.content
    assert "Project: Website" in text
    assert "**Identifier:** website" in text
    assert "Company website project." in text


@respx.mock
async def test_read_issue_resource_not_found(mcp: FastMCP, bound_client: RedmineClient) -> None:
    respx.get(f"{BASE}/issues/999.json").mock(return_value=httpx.Response(404))

    with pytest.raises(ValueError):  # raised by FastMCP template creation
        await mcp.read_resource(f"{BASE}/issues/999")
