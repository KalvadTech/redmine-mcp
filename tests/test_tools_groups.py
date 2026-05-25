from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_groups(mcp) -> None:
    respx.get(f"{BASE_URL}/groups.json").mock(
        return_value=httpx.Response(200, json={"groups": [{"id": 1, "name": "Backend"}]})
    )
    out = await call(mcp, "list_groups")
    assert out["items"] == [{"id": 1, "name": "Backend"}]


@respx.mock
async def test_get_group_with_include(mcp) -> None:
    route = respx.get(f"{BASE_URL}/groups/1.json").mock(
        return_value=httpx.Response(
            200,
            json={"group": {"id": 1, "name": "Backend", "users": [{"id": 5, "name": "ada"}]}},
        )
    )
    out = await call(mcp, "get_group", id=1, include=["users"])
    assert out["users"][0]["name"] == "ada"
    assert route.calls.last.request.url.params["include"] == "users"


@respx.mock
async def test_create_group_with_users(mcp) -> None:
    route = respx.post(f"{BASE_URL}/groups.json").mock(
        return_value=httpx.Response(201, json={"group": {"id": 2}})
    )
    out = await call(mcp, "create_group", name="Frontend", user_ids=[1, 2])
    assert out == {"id": 2}
    body = route.calls.last.request.read()
    assert b'"name":"Frontend"' in body
    assert b'"user_ids":[1,2]' in body


@respx.mock
async def test_update_group(mcp) -> None:
    route = respx.put(f"{BASE_URL}/groups/2.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "update_group", id=2, name="Web")
    assert out == {"id": 2, "updated": True}
    assert b'"name":"Web"' in route.calls.last.request.read()


@respx.mock
async def test_delete_group(mcp) -> None:
    respx.delete(f"{BASE_URL}/groups/2.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "delete_group", id=2)
    assert out == {"id": 2, "deleted": True}


@respx.mock
async def test_add_user_to_group(mcp) -> None:
    route = respx.post(f"{BASE_URL}/groups/1/users.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "add_user_to_group", group_id=1, user_id=42)
    assert out == {"group_id": 1, "user_id": 42, "added": True}
    assert b'"user_id":42' in route.calls.last.request.read()


@respx.mock
async def test_remove_user_from_group(mcp) -> None:
    respx.delete(f"{BASE_URL}/groups/1/users/42.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "remove_user_from_group", group_id=1, user_id=42)
    assert out == {"group_id": 1, "user_id": 42, "removed": True}
