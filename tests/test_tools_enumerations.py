from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_issue_priorities(mcp) -> None:
    respx.get(f"{BASE_URL}/enumerations/issue_priorities.json").mock(
        return_value=httpx.Response(
            200, json={"issue_priorities": [{"id": 1, "name": "Low"}, {"id": 2, "name": "Normal"}]}
        )
    )
    out = await call(mcp, "list_issue_priorities")
    assert [p["name"] for p in out["items"]] == ["Low", "Normal"]


@respx.mock
async def test_list_time_entry_activities(mcp) -> None:
    respx.get(f"{BASE_URL}/enumerations/time_entry_activities.json").mock(
        return_value=httpx.Response(
            200, json={"time_entry_activities": [{"id": 9, "name": "Development"}]}
        )
    )
    out = await call(mcp, "list_time_entry_activities")
    assert out["items"][0]["id"] == 9


@respx.mock
async def test_list_document_categories(mcp) -> None:
    respx.get(f"{BASE_URL}/enumerations/document_categories.json").mock(
        return_value=httpx.Response(
            200, json={"document_categories": [{"id": 1, "name": "Docs"}]}
        )
    )
    out = await call(mcp, "list_document_categories")
    assert out["items"] == [{"id": 1, "name": "Docs"}]
