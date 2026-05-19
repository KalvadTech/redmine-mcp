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
    route = respx.put(f"{BASE_URL}/issues/3.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "update_issue", id=3, notes="ack")
    assert out == {"id": 3, "updated": True}
    assert b'"notes":"ack"' in route.calls.last.request.read()


@respx.mock
async def test_add_issue_note_uses_put(mcp) -> None:
    route = respx.put(f"{BASE_URL}/issues/9.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "add_issue_note", id=9, notes="hi", private=True)
    assert out["noted"] is True
    body = route.calls.last.request.read()
    assert b'"private_notes":true' in body


@respx.mock
async def test_delete_issue(mcp) -> None:
    respx.delete(f"{BASE_URL}/issues/5.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "delete_issue", id=5)
    assert out == {"id": 5, "deleted": True}


@respx.mock
async def test_create_issue_with_uploads_and_custom_fields(mcp) -> None:
    route = respx.post(f"{BASE_URL}/issues.json").mock(
        return_value=httpx.Response(201, json={"issue": {"id": 11}})
    )
    await call(
        mcp,
        "create_issue",
        project_id="p",
        subject="hi",
        custom_fields=[{"id": 1, "value": "foo"}],
        watcher_user_ids=[2, 3],
        uploads=[{"token": "abc.def", "filename": "x.txt", "content_type": "text/plain"}],
    )
    body = route.calls.last.request.read()
    assert b'"custom_fields":[{"id":1,"value":"foo"}]' in body
    assert b'"watcher_user_ids":[2,3]' in body
    assert b'"uploads":[{"token":"abc.def"' in body


@respx.mock
async def test_update_issue_422_surfaces_errors(mcp) -> None:
    respx.put(f"{BASE_URL}/issues/3.json").mock(
        return_value=httpx.Response(422, json={"errors": ["Subject can't be blank"]})
    )
    with pytest.raises(Exception, match="Subject can't be blank"):
        await call(mcp, "update_issue", id=3, subject="")


@respx.mock
async def test_get_issue_404_surfaces(mcp) -> None:
    respx.get(f"{BASE_URL}/issues/999.json").mock(return_value=httpx.Response(404))
    with pytest.raises(Exception, match="not found"):
        await call(mcp, "get_issue", id=999)


@respx.mock
async def test_update_issue_dates_progress_estimate(mcp) -> None:
    route = respx.put(f"{BASE_URL}/issues/3.json").mock(return_value=httpx.Response(204))
    out = await call(
        mcp,
        "update_issue",
        id=3,
        start_date="2026-05-01",
        due_date="2026-05-31",
        done_ratio=40,
        estimated_hours=8.5,
        is_private=True,
        version_id=12,
    )
    assert out == {"id": 3, "updated": True}
    body = route.calls.last.request.read()
    assert b'"start_date":"2026-05-01"' in body
    assert b'"due_date":"2026-05-31"' in body
    assert b'"done_ratio":40' in body
    assert b'"estimated_hours":8.5' in body
    assert b'"is_private":true' in body
    assert b'"fixed_version_id":12' in body


@respx.mock
async def test_create_issue_with_dates_and_version(mcp) -> None:
    route = respx.post(f"{BASE_URL}/issues.json").mock(
        return_value=httpx.Response(201, json={"issue": {"id": 21}})
    )
    await call(
        mcp,
        "create_issue",
        project_id="p",
        subject="schedule",
        start_date="2026-06-01",
        due_date="2026-06-15",
        version_id=7,
    )
    body = route.calls.last.request.read()
    assert b'"start_date":"2026-06-01"' in body
    assert b'"due_date":"2026-06-15"' in body
    assert b'"fixed_version_id":7' in body
