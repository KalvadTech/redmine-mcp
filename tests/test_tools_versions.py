from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_versions(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/p/versions.json").mock(
        return_value=httpx.Response(
            200, json={"versions": [{"id": 1, "name": "v1"}], "total_count": 1}
        )
    )
    out = await call(mcp, "list_versions", project_id="p")
    assert out == {"items": [{"id": 1, "name": "v1"}], "total_count": 1}


@respx.mock
async def test_get_version(mcp) -> None:
    respx.get(f"{BASE_URL}/versions/1.json").mock(
        return_value=httpx.Response(200, json={"version": {"id": 1, "name": "v1"}})
    )
    out = await call(mcp, "get_version", id=1)
    assert out == {"id": 1, "name": "v1"}


@respx.mock
async def test_create_version(mcp) -> None:
    route = respx.post(f"{BASE_URL}/projects/p/versions.json").mock(
        return_value=httpx.Response(201, json={"version": {"id": 5}})
    )
    out = await call(
        mcp,
        "create_version",
        project_id="p",
        name="2.0",
        status="open",
        sharing="descendants",
        due_date="2026-12-31",
    )
    assert out == {"id": 5}
    body = route.calls.last.request.read()
    assert b'"name":"2.0"' in body
    assert b'"status":"open"' in body
    assert b'"sharing":"descendants"' in body
    assert b'"due_date":"2026-12-31"' in body


@respx.mock
async def test_update_version(mcp) -> None:
    route = respx.put(f"{BASE_URL}/versions/5.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "update_version", id=5, status="closed")
    assert out == {"id": 5, "updated": True}
    body = route.calls.last.request.read()
    assert b'"status":"closed"' in body
    assert b'"name"' not in body


@respx.mock
async def test_delete_version(mcp) -> None:
    respx.delete(f"{BASE_URL}/versions/5.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "delete_version", id=5)
    assert out == {"id": 5, "deleted": True}
