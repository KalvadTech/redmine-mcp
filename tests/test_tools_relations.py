from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_issue_relations(mcp) -> None:
    respx.get(f"{BASE_URL}/issues/1/relations.json").mock(
        return_value=httpx.Response(
            200, json={"relations": [{"id": 100, "issue_id": 1, "issue_to_id": 2}]}
        )
    )
    out = await call(mcp, "list_issue_relations", issue_id=1)
    assert out["items"][0]["issue_to_id"] == 2


@respx.mock
async def test_get_relation(mcp) -> None:
    respx.get(f"{BASE_URL}/relations/100.json").mock(
        return_value=httpx.Response(200, json={"relation": {"id": 100}})
    )
    out = await call(mcp, "get_relation", id=100)
    assert out == {"id": 100}


@respx.mock
async def test_create_issue_relation_default_type(mcp) -> None:
    route = respx.post(f"{BASE_URL}/issues/1/relations.json").mock(
        return_value=httpx.Response(201, json={"relation": {"id": 100}})
    )
    out = await call(mcp, "create_issue_relation", issue_id=1, issue_to_id=2)
    assert out == {"id": 100}
    body = route.calls.last.request.read()
    assert b'"issue_to_id":2' in body
    assert b'"relation_type":"relates"' in body


@respx.mock
async def test_create_issue_relation_precedes_with_delay(mcp) -> None:
    route = respx.post(f"{BASE_URL}/issues/1/relations.json").mock(
        return_value=httpx.Response(201, json={"relation": {"id": 101}})
    )
    await call(
        mcp,
        "create_issue_relation",
        issue_id=1,
        issue_to_id=2,
        relation_type="precedes",
        delay=3,
    )
    body = route.calls.last.request.read()
    assert b'"relation_type":"precedes"' in body
    assert b'"delay":3' in body


@respx.mock
async def test_delete_relation(mcp) -> None:
    respx.delete(f"{BASE_URL}/relations/100.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "delete_relation", id=100)
    assert out == {"id": 100, "deleted": True}
