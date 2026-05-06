from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_my_account() -> dict[str, Any]:
        """Get the authenticated user's full account record (richer than
        get_user('current')). Includes preferences and custom fields."""
        data = await client().get_json("/my/account.json")
        return data.get("user", data)

    @mcp.tool()
    async def update_my_account(
        firstname: str | None = None,
        lastname: str | None = None,
        mail: str | None = None,
        language: str | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update the authenticated user's account.

        custom_fields entries: {"id": int, "value": str | list[str]}.
        """
        body: dict[str, Any] = {}
        for key, value in {
            "firstname": firstname,
            "lastname": lastname,
            "mail": mail,
            "language": language,
        }.items():
            if value is not None:
                body[key] = value
        if custom_fields is not None:
            body["custom_fields"] = custom_fields
        await client().put_json("/my/account.json", json={"user": body})
        return {"updated": True}
