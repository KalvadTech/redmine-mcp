from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_news_cross_project(mcp) -> None:
    respx.get(f"{BASE_URL}/news.json").mock(
        return_value=httpx.Response(
            200,
            json={"news": [{"id": 1, "title": "hi"}], "total_count": 1, "limit": 25, "offset": 0},
        )
    )
    out = await call(mcp, "list_news")
    assert out["items"] == [{"id": 1, "title": "hi"}]


@respx.mock
async def test_list_news_per_project(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/p/news.json").mock(
        return_value=httpx.Response(200, json={"news": [], "total_count": 0})
    )
    out = await call(mcp, "list_news", project_id="p")
    assert out == {"items": [], "total_count": 0, "limit": 25, "offset": 0}
