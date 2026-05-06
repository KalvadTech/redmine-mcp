from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_roles(mcp) -> None:
    respx.get(f"{BASE_URL}/roles.json").mock(
        return_value=httpx.Response(
            200, json={"roles": [{"id": 3, "name": "Developer"}, {"id": 4, "name": "Reporter"}]}
        )
    )
    out = await call(mcp, "list_roles")
    assert [r["name"] for r in out["items"]] == ["Developer", "Reporter"]


@respx.mock
async def test_get_role_includes_permissions(mcp) -> None:
    respx.get(f"{BASE_URL}/roles/3.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "role": {
                    "id": 3,
                    "name": "Developer",
                    "permissions": ["view_issues", "edit_issues"],
                }
            },
        )
    )
    out = await call(mcp, "get_role", id=3)
    assert "edit_issues" in out["permissions"]
