from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_queries(mcp) -> None:
    respx.get(f"{BASE_URL}/queries.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "queries": [{"id": 1, "name": "Open"}, {"id": 2, "name": "Mine"}],
                "total_count": 2,
                "limit": 25,
                "offset": 0,
            },
        )
    )
    out = await call(mcp, "list_queries")
    assert [q["name"] for q in out["items"]] == ["Open", "Mine"]
