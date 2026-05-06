from mcp.server.fastmcp import FastMCP

from . import (
    attachments,
    enumerations,
    issues,
    metadata,
    projects,
    search,
    time_entries,
    users,
    wiki,
)


def register_all(mcp: FastMCP) -> None:
    metadata.register(mcp)
    enumerations.register(mcp)
    projects.register(mcp)
    users.register(mcp)
    issues.register(mcp)
    time_entries.register(mcp)
    search.register(mcp)
    wiki.register(mcp)
    attachments.register(mcp)
