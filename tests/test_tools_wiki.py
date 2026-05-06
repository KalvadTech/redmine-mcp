from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_wiki_pages(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/p/wiki/index.json").mock(
        return_value=httpx.Response(
            200, json={"wiki_pages": [{"title": "Home"}, {"title": "API"}]}
        )
    )
    out = await call(mcp, "list_wiki_pages", project_id="p")
    assert out["items"][0]["title"] == "Home"


@respx.mock
async def test_get_wiki_page_with_version(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/p/wiki/Some%20Page/3.json").mock(
        return_value=httpx.Response(200, json={"wiki_page": {"title": "Some Page", "version": 3}})
    )
    out = await call(mcp, "get_wiki_page", project_id="p", title="Some Page", version=3)
    assert out["version"] == 3


@respx.mock
async def test_create_or_update_wiki_page(mcp) -> None:
    route = respx.put(f"{BASE_URL}/projects/p/wiki/Home.json").mock(
        return_value=httpx.Response(204)
    )
    out = await call(
        mcp,
        "create_or_update_wiki_page",
        project_id="p",
        title="Home",
        text="hello",
        comments="initial",
    )
    assert out["saved"] is True
    body = route.calls.last.request.read()
    assert b'"text":"hello"' in body
    assert b'"comments":"initial"' in body


@respx.mock
async def test_delete_wiki_page(mcp) -> None:
    respx.delete(f"{BASE_URL}/projects/p/wiki/Old.json").mock(
        return_value=httpx.Response(204)
    )
    out = await call(mcp, "delete_wiki_page", project_id="p", title="Old")
    assert out == {"project_id": "p", "title": "Old", "deleted": True}
