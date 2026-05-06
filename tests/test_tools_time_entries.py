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
