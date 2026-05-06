from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_search_basic(mcp) -> None:
    respx.get(f"{BASE_URL}/search.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [{"id": 1, "title": "x"}],
                "total_count": 1,
                "limit": 25,
                "offset": 0,
            },
        )
    )
    out = await call(mcp, "search", q="hello")
    assert out["items"] == [{"id": 1, "title": "x"}]


@respx.mock
async def test_search_with_filters_and_booleans(mcp) -> None:
    route = respx.get(f"{BASE_URL}/search.json").mock(
        return_value=httpx.Response(200, json={"results": [], "total_count": 0})
    )
    await call(
        mcp,
        "search",
        q="hello",
        scope="my_project",
        all_words=True,
        titles_only=False,
        issues=True,
        wiki_pages=True,
        open_issues=False,
        attachments="only",
        project_id="myproj",
    )
    p = route.calls.last.request.url.params
    assert p["q"] == "hello"
    assert p["scope"] == "my_project"
    assert p["all_words"] == "1"
    assert p["titles_only"] == "0"
    assert p["issues"] == "1"
    assert p["wiki_pages"] == "1"
    assert p["open_issues"] == "0"
    assert p["attachments"] == "only"
    assert p["project_id"] == "myproj"


@respx.mock
async def test_search_omits_unset_booleans(mcp) -> None:
    route = respx.get(f"{BASE_URL}/search.json").mock(
        return_value=httpx.Response(200, json={"results": [], "total_count": 0})
    )
    await call(mcp, "search", q="x")
    p = route.calls.last.request.url.params
    assert "all_words" not in p
    assert "titles_only" not in p
    assert "issues" not in p
