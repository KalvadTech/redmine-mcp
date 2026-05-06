from __future__ import annotations

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_update_journal_note(mcp) -> None:
    route = respx.put(f"{BASE_URL}/journals/55.json").mock(return_value=httpx.Response(204))
    out = await call(mcp, "update_journal_note", id=55, notes="rev2", private_notes=True)
    assert out == {"id": 55, "updated": True}
    body = route.calls.last.request.read()
    assert b'"notes":"rev2"' in body
    assert b'"private_notes":true' in body


@respx.mock
async def test_update_journal_note_omits_unset_privacy(mcp) -> None:
    route = respx.put(f"{BASE_URL}/journals/55.json").mock(return_value=httpx.Response(204))
    await call(mcp, "update_journal_note", id=55, notes="hi")
    body = route.calls.last.request.read()
    assert b'"notes":"hi"' in body
    assert b"private_notes" not in body
