from __future__ import annotations

import httpx
import pytest
import respx

from redmine_mcp.client import RedmineClient
from redmine_mcp.errors import RedmineError

BASE = "https://redmine.test"
KEY = "x" * 40


@respx.mock
async def test_paginate_returns_envelope() -> None:
    respx.get(f"{BASE}/issues.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "issues": [{"id": 1}, {"id": 2}],
                "total_count": 42,
                "limit": 25,
                "offset": 0,
            },
        )
    )
    async with RedmineClient(BASE, KEY) as c:
        page = await c.paginate("/issues.json", "issues")
    assert page == {
        "items": [{"id": 1}, {"id": 2}],
        "total_count": 42,
        "limit": 25,
        "offset": 0,
    }


@respx.mock
async def test_iter_all_walks_pages() -> None:
    respx.get(f"{BASE}/issues.json", params={"limit": "100", "offset": "0"}).mock(
        return_value=httpx.Response(
            200,
            json={"issues": [{"id": i} for i in range(100)], "total_count": 150},
        )
    )
    respx.get(f"{BASE}/issues.json", params={"limit": "100", "offset": "100"}).mock(
        return_value=httpx.Response(
            200,
            json={"issues": [{"id": i} for i in range(100, 150)], "total_count": 150},
        )
    )
    async with RedmineClient(BASE, KEY) as c:
        items = [item async for item in c.iter_all("/issues.json", "issues")]
    assert len(items) == 150
    assert items[0]["id"] == 0
    assert items[-1]["id"] == 149


@respx.mock
async def test_401_maps_to_redmine_error() -> None:
    respx.get(f"{BASE}/users/current.json").mock(return_value=httpx.Response(401))
    async with RedmineClient(BASE, KEY) as c:
        with pytest.raises(RedmineError) as info:
            await c.get_json("/users/current.json")
    assert info.value.status == 401
    assert "unauthorized" in str(info.value).lower() or "invalid" in str(info.value).lower()


@respx.mock
async def test_422_surfaces_redmine_errors_list() -> None:
    respx.post(f"{BASE}/issues.json").mock(
        return_value=httpx.Response(
            422, json={"errors": ["Subject can't be blank", "Project is invalid"]}
        )
    )
    async with RedmineClient(BASE, KEY) as c:
        with pytest.raises(RedmineError) as info:
            await c.post_json("/issues.json", json={"issue": {}})
    assert info.value.status == 422
    assert info.value.errors == ["Subject can't be blank", "Project is invalid"]


@respx.mock
async def test_get_bytes_caps_size() -> None:
    respx.get("https://files.test/big.bin").mock(
        return_value=httpx.Response(200, content=b"A" * 2048)
    )
    async with RedmineClient(BASE, KEY) as c:
        with pytest.raises(RedmineError) as info:
            await c.get_bytes("https://files.test/big.bin", max_bytes=1024)
    assert info.value.status == 413


@respx.mock
async def test_clean_params_drops_none() -> None:
    route = respx.get(f"{BASE}/issues.json").mock(
        return_value=httpx.Response(200, json={"issues": []})
    )
    async with RedmineClient(BASE, KEY) as c:
        await c.get_json("/issues.json", params={"project_id": None, "status_id": "open"})
    assert route.called
    sent = route.calls.last.request
    assert "project_id" not in sent.url.params
    assert sent.url.params["status_id"] == "open"


@respx.mock
async def test_sends_api_key_header() -> None:
    route = respx.get(f"{BASE}/users/current.json").mock(
        return_value=httpx.Response(200, json={"user": {"id": 1}})
    )
    async with RedmineClient(BASE, KEY) as c:
        await c.get_json("/users/current.json")
    assert route.calls.last.request.headers["X-Redmine-API-Key"] == KEY
