from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_get_my_account(mcp) -> None:
    respx.get(f"{BASE_URL}/my/account.json").mock(
        return_value=httpx.Response(
            200,
            json={"user": {"id": 99, "login": "ada", "mail": "ada@example.com"}},
        )
    )
    out = await call(mcp, "get_my_account")
    assert out["login"] == "ada"


@respx.mock
async def test_update_my_account(mcp) -> None:
    route = respx.put(f"{BASE_URL}/my/account.json").mock(return_value=httpx.Response(204))
    out = await call(
        mcp,
        "update_my_account",
        firstname="Ada",
        lastname="Lovelace",
        mail="ada@example.com",
        custom_fields=[{"id": 7, "value": "math"}],
    )
    assert out == {"updated": True}
    body = route.calls.last.request.read()
    assert b'"firstname":"Ada"' in body
    assert b'"lastname":"Lovelace"' in body
    assert b'"mail":"ada@example.com"' in body
    assert b'"custom_fields":[{"id":7,"value":"math"}]' in body
