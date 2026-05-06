from mcp.server.fastmcp import FastMCP

from . import (
    attachments,
    enumerations,
    files,
    groups,
    issues,
    journals,
    memberships,
    metadata,
    my_account,
    news,
    projects,
    queries,
    relations,
    roles,
    search,
    time_entries,
    users,
    versions,
    wiki,
)


def register_all(mcp: FastMCP) -> None:
    metadata.register(mcp)
    enumerations.register(mcp)
    projects.register(mcp)
    memberships.register(mcp)
    users.register(mcp)
    my_account.register(mcp)
    groups.register(mcp)
    roles.register(mcp)
    issues.register(mcp)
    relations.register(mcp)
    journals.register(mcp)
    versions.register(mcp)
    queries.register(mcp)
    time_entries.register(mcp)
    news.register(mcp)
    search.register(mcp)
    wiki.register(mcp)
    attachments.register(mcp)
    files.register(mcp)
