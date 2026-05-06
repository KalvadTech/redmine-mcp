from __future__ import annotations

import base64

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_get_attachment(mcp) -> None:
    respx.get(f"{BASE_URL}/attachments/1.json").mock(
        return_value=httpx.Response(
            200,
            json={"attachment": {"id": 1, "filename": "a.txt", "content_url": "..."}},
        )
    )
    out = await call(mcp, "get_attachment", id=1)
    assert out["id"] == 1


@respx.mock
async def test_download_attachment_returns_base64(mcp) -> None:
    respx.get(f"{BASE_URL}/attachments/2.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "attachment": {
                    "id": 2,
                    "filename": "hello.txt",
                    "content_url": "https://files.test/hello.txt",
                }
            },
        )
    )
    respx.get("https://files.test/hello.txt").mock(
        return_value=httpx.Response(
            200,
            content=b"hello world",
            headers={"Content-Type": "text/plain"},
        )
    )
    out = await call(mcp, "download_attachment", id=2)
    assert out["filename"] == "hello.txt"
    assert out["content_type"] == "text/plain"
    assert base64.b64decode(out["content_base64"]) == b"hello world"


@respx.mock
async def test_upload_attachment(mcp) -> None:
    route = respx.post(f"{BASE_URL}/uploads.json", params={"filename": "x.bin"}).mock(
        return_value=httpx.Response(201, json={"upload": {"token": "abc.def"}})
    )
    payload = base64.b64encode(b"raw bytes").decode("ascii")
    out = await call(
        mcp,
        "upload_attachment",
        filename="x.bin",
        content_base64=payload,
        content_type="application/octet-stream",
    )
    assert out == {
        "token": "abc.def",
        "filename": "x.bin",
        "content_type": "application/octet-stream",
        "size": 9,
    }
    sent = route.calls.last.request
    assert sent.headers["Content-Type"] == "application/octet-stream"
    assert sent.read() == b"raw bytes"
