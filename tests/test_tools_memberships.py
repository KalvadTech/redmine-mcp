from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_get_membership(mcp) -> None:
    respx.get(f"{BASE_URL}/memberships/12.json").mock(
        return_value=httpx.Response(200, json={"membership": {"id": 12}})
    )
    out = await call(mcp, "get_membership", id=12)
    assert out == {"id": 12}


@respx.mock
async def test_add_project_member_user(mcp) -> None:
    route = respx.post(f"{BASE_URL}/projects/p/memberships.json").mock(
        return_value=httpx.Response(201, json={"membership": {"id": 7}})
    )
    out = await call(mcp, "add_project_member", project_id="p", user_id=42, role_ids=[3])
    assert out == {"id": 7}
    body = route.calls.last.request.read()
    assert b'"user_id":42' in body
    assert b'"role_ids":[3]' in body


@respx.mock
async def test_add_project_member_group(mcp) -> None:
    route = respx.post(f"{BASE_URL}/projects/p/memberships.json").mock(
        return_value=httpx.Response(201, json={"membership": {"id": 8}})
    )
    await call(mcp, "add_project_member", project_id="p", group_id=99, role_ids=[3, 4])
    body = route.calls.last.request.read()
    assert b'"group_id":99' in body
    assert b'"role_ids":[3,4]' in body


@respx.mock
async def test_add_project_member_requires_one_target(mcp) -> None:
    with pytest.raises(Exception, match="exactly one"):
        await call(mcp, "add_project_member", project_id="p", role_ids=[3])


@respx.mock
async def test_update_membership(mcp) -> None:
    route = respx.put(f"{BASE_URL}/memberships/12.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "update_membership", id=12, role_ids=[3, 5])
    assert out == {"id": 12, "updated": True}
    assert b'"role_ids":[3,5]' in route.calls.last.request.read()


@respx.mock
async def test_remove_membership(mcp) -> None:
    respx.delete(f"{BASE_URL}/memberships/12.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "remove_membership", id=12)
    assert out == {"id": 12, "deleted": True}
