from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from redmine_mcp.client import (
    RedmineClient,
    reset_current_client,
    set_current_client,
)
from redmine_mcp.resources import register as register_resources
from redmine_mcp.tools import register_all

BASE_URL = "https://redmine.test"
API_KEY = "1234567890abcdef1234567890abcdef12345678"


@pytest.fixture
def mcp() -> FastMCP:
    server = FastMCP("redmine-test")
    register_all(server)
    register_resources(server, BASE_URL)
    return server


@pytest.fixture
async def bound_client() -> AsyncIterator[RedmineClient]:
    client = RedmineClient(BASE_URL, API_KEY)
    token = set_current_client(client)
    try:
        yield client
    finally:
        reset_current_client(token)
        await client.aclose()


async def call(mcp: FastMCP, tool_name: str, /, **arguments: Any) -> Any:
    result = await mcp.call_tool(tool_name, arguments)
    if isinstance(result, tuple) and len(result) == 2:
        _, structured = result
        if structured is not None:
            return structured
        result = result[0]
    if isinstance(result, dict):
        return result
    if not result:
        return None
    block = result[0]
    if isinstance(block, TextContent):
        try:
            return json.loads(block.text)
        except json.JSONDecodeError:
            return block.text
    return block
