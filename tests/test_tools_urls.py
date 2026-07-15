from __future__ import annotations

import httpx
import respx

from redmine_mcp.client import RedmineClient
from tests.conftest import BASE_URL, call


@respx.mock
async def test_open_issue_url(mcp: object, bound_client: RedmineClient) -> None:
    respx.get(f"{BASE_URL}/issues/4085.json").mock(
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
                    "description": "Users cannot log in.",
                }
            },
        )
    )

    result = await call(mcp, "open_redmine_url", url=f"{BASE_URL}/issues/4085")
    text = result["result"] if isinstance(result, dict) else result
    assert isinstance(text, str)
    assert "Issue #4085: Fix login" in text
    assert "Users cannot log in." in text


@respx.mock
async def test_open_project_url(mcp: object, bound_client: RedmineClient) -> None:
    respx.get(f"{BASE_URL}/projects/website.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "project": {
                    "id": 1,
                    "name": "Website",
                    "identifier": "website",
                    "description": "Company website.",
                    "status": 1,
                }
            },
        )
    )

    result = await call(mcp, "open_redmine_url", url=f"{BASE_URL}/projects/website")
    text = result["result"] if isinstance(result, dict) else result
    assert isinstance(text, str)
    assert "Project: Website" in text
    assert "Company website." in text


@respx.mock
async def test_open_url_wrong_instance(mcp: object, bound_client: RedmineClient) -> None:
    result = await call(mcp, "open_redmine_url", url="https://other.redmine/issues/4085")
    text = result["result"] if isinstance(result, dict) else result
    assert isinstance(text, str)
    assert "does not belong to the configured Redmine instance" in text


@respx.mock
async def test_open_url_unsupported_path(mcp: object, bound_client: RedmineClient) -> None:
    result = await call(mcp, "open_redmine_url", url=f"{BASE_URL}/users/5")
    text = result["result"] if isinstance(result, dict) else result
    assert isinstance(text, str)
    assert "Unsupported Redmine URL" in text
