from __future__ import annotations

import base64

import httpx
import pytest
import respx

from .conftest import BASE_URL, call

pytestmark = pytest.mark.usefixtures("bound_client")


@respx.mock
async def test_list_files(mcp) -> None:
    respx.get(f"{BASE_URL}/projects/p/files.json").mock(
        return_value=httpx.Response(
            200, json={"files": [{"id": 1, "filename": "spec.pdf"}]}
        )
    )
    out = await call(mcp, "list_files", project_id="p")
    assert out["items"] == [{"id": 1, "filename": "spec.pdf"}]


@respx.mock
async def test_upload_file_two_step(mcp) -> None:
    upload_route = respx.post(
        f"{BASE_URL}/uploads.json", params={"filename": "spec.pdf"}
    ).mock(return_value=httpx.Response(201, json={"upload": {"token": "tok.123"}}))
    attach_route = respx.post(f"{BASE_URL}/projects/p/files.json").mock(
        return_value=httpx.Response(201, json={"file": {"id": 9}})
    )
    payload = base64.b64encode(b"PDF contents").decode("ascii")
    out = await call(
        mcp,
        "upload_file",
        project_id="p",
        filename="spec.pdf",
        content_base64=payload,
        content_type="application/pdf",
        description="design notes",
        version_id=3,
    )
    assert out["token"] == "tok.123"
    assert out["filename"] == "spec.pdf"
    assert out["size"] == 12
    assert upload_route.called and attach_route.called

    upload_sent = upload_route.calls.last.request
    assert upload_sent.headers["Content-Type"] == "application/pdf"
    assert upload_sent.read() == b"PDF contents"

    attach_body = attach_route.calls.last.request.read()
    assert b'"token":"tok.123"' in attach_body
    assert b'"description":"design notes"' in attach_body
    assert b'"version_id":3' in attach_body


@respx.mock
async def test_upload_file_rejects_bad_base64(mcp) -> None:
    with pytest.raises(Exception, match="base64"):
        await call(
            mcp,
            "upload_file",
            project_id="p",
            filename="x.bin",
            content_base64="not-valid!",
        )
