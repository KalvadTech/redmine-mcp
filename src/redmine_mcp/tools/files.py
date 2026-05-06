from __future__ import annotations

import base64
from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_files(project_id: int | str) -> dict[str, Any]:
        """List files attached to a project."""
        data = await client().get_json(f"/projects/{project_id}/files.json")
        return {"items": data.get("files", [])}

    @mcp.tool()
    async def upload_file(
        project_id: int | str,
        filename: str,
        content_base64: str,
        content_type: str = "application/octet-stream",
        description: str | None = None,
        version_id: int | None = None,
    ) -> dict[str, Any]:
        """Upload a file and attach it to a project's Files area in one
        call. Internally does POST /uploads.json then POST
        /projects/:id/files.json with the returned token. Use
        upload_attachment + create_issue/update_issue if you want the
        token attached to an issue instead."""
        try:
            content = base64.b64decode(content_base64, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("content_base64 is not valid base64") from exc

        c = client()
        upload = await c.post_octet_stream(
            "/uploads.json",
            content=content,
            params={"filename": filename},
            content_type=content_type,
        )
        token = (upload or {}).get("upload", {}).get("token")
        if not token:
            raise ValueError("upload returned no token")

        body: dict[str, Any] = {
            "token": token,
            "filename": filename,
            "content_type": content_type,
        }
        if description is not None:
            body["description"] = description
        if version_id is not None:
            body["version_id"] = version_id
        data = await c.post_json(
            f"/projects/{project_id}/files.json",
            json={"file": body},
        )
        return {
            "project_id": project_id,
            "filename": filename,
            "size": len(content),
            "token": token,
            "result": data,
        }
