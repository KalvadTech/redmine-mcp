from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_issue_statuses(mcp) -> None:
    respx.get(f"{BASE_URL}/issue_statuses.json").mock(
        return_value=httpx.Response(
            200, json={"issue_statuses": [{"id": 1, "name": "New"}, {"id": 5, "name": "Closed"}]}
        )
    )
    out = await call(mcp, "list_issue_statuses")
    assert out["items"][0]["name"] == "New"


@respx.mock
async def test_list_trackers(mcp) -> None:
    respx.get(f"{BASE_URL}/trackers.json").mock(
        return_value=httpx.Response(200, json={"trackers": [{"id": 1, "name": "Bug"}]})
    )
    out = await call(mcp, "list_trackers")
    assert out["items"] == [{"id": 1, "name": "Bug"}]


@respx.mock
async def test_list_issue_categories_for_project(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/p/issue_categories.json").mock(
        return_value=httpx.Response(200, json={"issue_categories": [{"id": 3, "name": "Backend"}]})
    )
    out = await call(mcp, "list_issue_categories", project_id="p")
    assert out["items"] == [{"id": 3, "name": "Backend"}]


@respx.mock
async def test_list_custom_fields_admin_only(mcp) -> None:
    respx.get(f"{BASE_URL}/custom_fields.json").mock(
        return_value=httpx.Response(403, json={"errors": ["Access forbidden"]})
    )
    with pytest.raises(Exception, match=r"403|forbid|Access"):
        await call(mcp, "list_custom_fields")
