from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_time_entries_with_date_range(mcp) -> None:
    route = respx.get(f"{BASE_URL}/time_entries.json").mock(
        return_value=httpx.Response(
            200,
            json={"time_entries": [], "total_count": 0, "limit": 25, "offset": 0},
        )
    )
    await call(
        mcp,
        "list_time_entries",
        spent_on_from="2026-01-01",
        spent_on_to="2026-01-31",
    )
    sent = route.calls.last.request
    assert sent.url.params["spent_on"] == "><2026-01-01|2026-01-31"


@respx.mock
async def test_create_time_entry_requires_one_target(mcp) -> None:
    with pytest.raises(Exception) as info:
        await call(
            mcp,
            "create_time_entry",
            hours=1.5,
            activity_id=9,
        )
    assert "exactly one" in str(info.value).lower()


@respx.mock
async def test_create_time_entry_on_issue(mcp) -> None:
    route = respx.post(f"{BASE_URL}/time_entries.json").mock(
        return_value=httpx.Response(201, json={"time_entry": {"id": 1, "hours": 1.5}})
    )
    out = await call(
        mcp,
        "create_time_entry",
        hours=1.5,
        activity_id=9,
        issue_id=42,
        comments="work",
    )
    assert out == {"id": 1, "hours": 1.5}
    body = route.calls.last.request.read()
    assert b'"issue_id":42' in body
    assert b'"hours":1.5' in body


@respx.mock
async def test_create_time_entry_on_project(mcp) -> None:
    route = respx.post(f"{BASE_URL}/time_entries.json").mock(
        return_value=httpx.Response(201, json={"time_entry": {"id": 2}})
    )
    await call(
        mcp,
        "create_time_entry",
        hours=2.0,
        activity_id=9,
        project_id="myproj",
        spent_on="2026-05-06",
    )
    body = route.calls.last.request.read()
    assert b'"project_id":"myproj"' in body
    assert b'"spent_on":"2026-05-06"' in body
    assert b"issue_id" not in body


@respx.mock
async def test_list_time_entries_only_from(mcp) -> None:
    route = respx.get(f"{BASE_URL}/time_entries.json").mock(
        return_value=httpx.Response(200, json={"time_entries": [], "total_count": 0})
    )
    await call(mcp, "list_time_entries", spent_on_from="2026-05-01")
    assert route.calls.last.request.url.params["spent_on"] == ">=2026-05-01"


@respx.mock
async def test_list_time_entries_only_to(mcp) -> None:
    route = respx.get(f"{BASE_URL}/time_entries.json").mock(
        return_value=httpx.Response(200, json={"time_entries": [], "total_count": 0})
    )
    await call(mcp, "list_time_entries", spent_on_to="2026-05-31")
    assert route.calls.last.request.url.params["spent_on"] == "<=2026-05-31"


@respx.mock
async def test_update_time_entry(mcp) -> None:
    route = respx.put(f"{BASE_URL}/time_entries/8.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "update_time_entry", id=8, hours=3.0, comments="rev")
    assert out == {"id": 8, "updated": True}
    body = route.calls.last.request.read()
    assert b'"hours":3.0' in body
    assert b'"comments":"rev"' in body


@respx.mock
async def test_delete_time_entry(mcp) -> None:
    respx.delete(f"{BASE_URL}/time_entries/8.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "delete_time_entry", id=8)
    assert out == {"id": 8, "deleted": True}
