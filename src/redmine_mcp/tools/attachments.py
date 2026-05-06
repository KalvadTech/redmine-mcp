from __future__ import annotations

import base64
from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client

_DEFAULT_MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
_HARD_MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_attachment(id: int) -> dict[str, Any]:
        """Get attachment metadata (filename, size, content_url, ...)."""
        data = await client().get_json(f"/attachments/{id}.json")
        return data.get("attachment", data)

    @mcp.tool()
    async def download_attachment(
        id: int,
        max_bytes: int | None = None,
    ) -> dict[str, Any]:
        """Download an attachment and return its content as base64.

        Capped at 25 MiB regardless of max_bytes. Use the streaming Redmine
        URL directly for larger files outside MCP.
        """
        cap = min(max_bytes or _DEFAULT_MAX_DOWNLOAD_BYTES, _HARD_MAX_DOWNLOAD_BYTES)
        c = client()
        meta = await c.get_json(f"/attachments/{id}.json")
        attachment = meta.get("attachment", meta)
        content_url = attachment.get("content_url")
        if not content_url:
            raise ValueError(f"attachment {id} has no content_url")
        content, content_type = await c.get_bytes(content_url, max_bytes=cap)
        return {
            "id": id,
            "filename": attachment.get("filename"),
            "content_type": content_type,
            "size": len(content),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }

    @mcp.tool()
    async def upload_attachment(
        filename: str,
        content_base64: str,
        content_type: str = "application/octet-stream",
    ) -> dict[str, Any]:
        """Upload a file and get a token. Pass the token in `uploads` on
        create_issue/update_issue to attach the file:

            uploads=[{"token": "<token>", "filename": "...",
                      "content_type": "...", "description": "..."}]
        """
        try:
            content = base64.b64decode(content_base64, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("content_base64 is not valid base64") from exc
        data = await client().post_octet_stream(
            "/uploads.json",
            content=content,
            params={"filename": filename},
            content_type=content_type,
        )
        upload = (data or {}).get("upload", {})
        return {
            "token": upload.get("token"),
            "filename": filename,
            "content_type": content_type,
            "size": len(content),
        }
