from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_projects_with_include(mcp) -> None:
    route = respx.get(f"{BASE_URL}/projects.json").mock(
        return_value=httpx.Response(
            200,
            json={"projects": [{"id": 1, "name": "p"}], "total_count": 1, "limit": 25, "offset": 0},
        )
    )
    out = await call(
        mcp, "list_projects", include=["trackers", "issue_categories"], limit=10, offset=5
    )
    assert out == {
        "items": [{"id": 1, "name": "p"}],
        "total_count": 1,
        "limit": 25,
        "offset": 0,
    }
    sent = route.calls.last.request
    assert sent.url.params["include"] == "trackers,issue_categories"
    assert sent.url.params["limit"] == "10"
    assert sent.url.params["offset"] == "5"


@respx.mock
async def test_list_projects_without_include_omits_param(mcp) -> None:
    route = respx.get(f"{BASE_URL}/projects.json").mock(
        return_value=httpx.Response(200, json={"projects": [], "total_count": 0})
    )
    await call(mcp, "list_projects")
    assert "include" not in route.calls.last.request.url.params


@respx.mock
async def test_get_project_by_identifier(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/myproj.json").mock(
        return_value=httpx.Response(200, json={"project": {"id": 7, "identifier": "myproj"}})
    )
    out = await call(mcp, "get_project", id="myproj", include=["enabled_modules"])
    assert out == {"id": 7, "identifier": "myproj"}


@respx.mock
async def test_get_project_unwraps_when_envelope_missing(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/12.json").mock(
        return_value=httpx.Response(200, json={"id": 12, "name": "x"})
    )
    out = await call(mcp, "get_project", id=12)
    assert out == {"id": 12, "name": "x"}


@respx.mock
async def test_list_memberships(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/p/memberships.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "memberships": [{"id": 1}, {"id": 2}],
                "total_count": 2,
                "limit": 25,
                "offset": 0,
            },
        )
    )
    out = await call(mcp, "list_memberships", project_id="p")
    assert out["items"] == [{"id": 1}, {"id": 2}]
    assert out["total_count"] == 2
