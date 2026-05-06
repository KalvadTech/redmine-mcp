from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_issues_filters(mcp) -> None:
    route = respx.get(f"{BASE_URL}/issues.json").mock(
        return_value=httpx.Response(
            200,
            json={"issues": [{"id": 1}], "total_count": 1, "limit": 25, "offset": 0},
        )
    )
    out = await call(
        mcp,
        "list_issues",
        project_id="myproj",
        status_id="open",
        assigned_to_id="me",
        include=["attachments", "relations"],
    )
    assert out["items"] == [{"id": 1}]
    sent = route.calls.last.request
    assert sent.url.params["project_id"] == "myproj"
    assert sent.url.params["status_id"] == "open"
    assert sent.url.params["assigned_to_id"] == "me"
    assert sent.url.params["include"] == "attachments,relations"


@respx.mock
async def test_get_issue(mcp) -> None:
    respx.get(f"{BASE_URL}/issues/42.json").mock(
        return_value=httpx.Response(200, json={"issue": {"id": 42, "subject": "x"}})
    )
    out = await call(mcp, "get_issue", id=42, include=["journals"])
    assert out == {"id": 42, "subject": "x"}


@respx.mock
async def test_create_issue_strips_none(mcp) -> None:
    route = respx.post(f"{BASE_URL}/issues.json").mock(
        return_value=httpx.Response(201, json={"issue": {"id": 7}})
    )
    out = await call(
        mcp,
        "create_issue",
        project_id="myproj",
        subject="Hello",
    )
    assert out == {"id": 7}
    body = route.calls.last.request.read()
    assert b'"subject":"Hello"' in body
    assert b"description" not in body


@respx.mock
async def test_update_issue_with_notes(mcp) -> None:
    route = respx.put(f"{BASE_URL}/issues/3.json").mock(
        return_value=httpx.Response(204)
    )
    out = await call(mcp, "update_issue", id=3, notes="ack")
    assert out == {"id": 3, "updated": True}
    assert b'"notes":"ack"' in route.calls.last.request.read()


@respx.mock
async def test_add_issue_note_uses_put(mcp) -> None:
    route = respx.put(f"{BASE_URL}/issues/9.json").mock(
        return_value=httpx.Response(204)
    )
    out = await call(mcp, "add_issue_note", id=9, notes="hi", private=True)
    assert out["noted"] is True
    body = route.calls.last.request.read()
    assert b'"private_notes":true' in body


@respx.mock
async def test_delete_issue(mcp) -> None:
    respx.delete(f"{BASE_URL}/issues/5.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "delete_issue", id=5)
    assert out == {"id": 5, "deleted": True}
