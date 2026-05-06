# redmine-mcp

Stateless MCP server for Redmine. Each request carries the user's own API key.
No database. No per-user server state. One process serves many Redmine instances
and many users at once.

## Auth

The Redmine base URL is fixed per deployment via the `REDMINE_URL` env var,
not provided by clients. Each MCP request carries only the user's own API
key:

- `X-Redmine-API-Key` (header) - the user's Redmine API key
  (find it in `My account > API access key`).

The server forwards the API key to Redmine as `X-Redmine-API-Key` (so it does
not land in Redmine access logs) and never persists it. There is no shared
service key. One server instance proxies one Redmine instance.

## Run

```sh
uv sync
REDMINE_URL=https://redmine.example.com \
  uv run redmine-mcp --host 127.0.0.1 --port 8080
```

The MCP endpoint is `http://127.0.0.1:8080/mcp`.

## Use from Claude Code

`.mcp.json`:

```json
{
  "mcpServers": {
    "redmine": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "X-Redmine-API-Key": "your-40-char-key"
      }
    }
  }
}
```

## Tools (v1)

Issues, projects, users, time entries, wiki, attachments, search, issue
categories, statuses, trackers, custom fields, and enumerations (priorities,
activities, document categories). All list tools return
`{items, total_count, limit, offset}`.

## Develop

```sh
uv run pytest
uv run ruff check .
uv run mypy src
```
