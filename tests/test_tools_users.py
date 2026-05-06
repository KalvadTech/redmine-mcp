from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_users_with_filters(mcp) -> None:
    route = respx.get(f"{BASE_URL}/users.json").mock(
        return_value=httpx.Response(
            200, json={"users": [{"id": 1}], "total_count": 1, "limit": 25, "offset": 0}
        )
    )
    await call(mcp, "list_users", name="ada", status=1, group_id=42)
    sent = route.calls.last.request
    assert sent.url.params["name"] == "ada"
    assert sent.url.params["status"] == "1"
    assert sent.url.params["group_id"] == "42"


@respx.mock
async def test_get_user_current(mcp) -> None:
    respx.get(f"{BASE_URL}/users/current.json").mock(
        return_value=httpx.Response(200, json={"user": {"id": 99, "login": "ada"}})
    )
    out = await call(mcp, "get_user", id_or_current="current")
    assert out == {"id": 99, "login": "ada"}


@respx.mock
async def test_get_user_by_id(mcp) -> None:
    respx.get(f"{BASE_URL}/users/7.json").mock(
        return_value=httpx.Response(200, json={"user": {"id": 7}})
    )
    out = await call(mcp, "get_user", id_or_current=7)
    assert out == {"id": 7}
