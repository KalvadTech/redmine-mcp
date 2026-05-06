# redmine-mcp

[![ci](https://github.com/KalvadTech/redmine-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/KalvadTech/redmine-mcp/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![container](https://img.shields.io/badge/container-ghcr.io-2496ED.svg)](https://github.com/KalvadTech/redmine-mcp/pkgs/container/redmine-mcp)

A stateless [Model Context Protocol](https://modelcontextprotocol.io) server
for [Redmine](https://www.redmine.org). Drop it in front of any Redmine
instance and let Claude (or any MCP-aware LLM client) read and write issues,
log time, browse the wiki, and search projects on behalf of the user, with
each user's own API key.

- **Zero state**: no database, no sessions, no shared secret. The server
  forwards each request to Redmine using the API key that came in with it.
- **One server, many users**: the only thing the operator configures is the
  upstream `REDMINE_URL`. Each MCP client supplies its own
  `X-Redmine-API-Key`. Permissions are whatever Redmine says they are.
- **Coverage**: issues (CRUD + notes), projects, memberships, users, time
  entries, wiki (PUT-upsert), attachments (upload + download), full-text
  search, statuses, trackers, categories, custom fields, enumerations.

## Quick start

### Local (uv)

```sh
uv sync
REDMINE_URL=https://redmine.example.com uv run redmine-mcp
```

The MCP endpoint is now at `http://127.0.0.1:8080/mcp`.

### Container (GHCR)

```sh
docker run --rm -p 8080:8080 \
  -e REDMINE_URL=https://redmine.example.com \
  ghcr.io/kalvadtech/redmine-mcp:latest
```

The image is multi-stage Alpine, runs as a non-root user, and exposes 8080.

## Wire it into your MCP client

Find your Redmine API key in `My account > API access key`. Both clients
below talk to the same MCP endpoint over Streamable HTTP; no other client
configuration is required.

### Claude Code

`.mcp.json` in your project root:

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

### opencode

`opencode.json` in your project root (or your opencode config directory):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "redmine": {
      "type": "remote",
      "url": "http://127.0.0.1:8080/mcp",
      "enabled": true,
      "headers": {
        "X-Redmine-API-Key": "{env:REDMINE_API_KEY}"
      }
    }
  }
}
```

opencode supports `{env:VAR}` interpolation in `headers`, so the API key
stays out of the config file: `REDMINE_API_KEY=... opencode`.

## Configuration

| Variable      | Required | Default | Purpose                                          |
| ------------- | -------- | ------- | ------------------------------------------------ |
| `REDMINE_URL` | yes      | -       | Base URL of the Redmine instance (http or https) |

CLI flags on `redmine-mcp`:

```text
--host        bind address (default 127.0.0.1)
--port        port (default 8080)
--log-level   uvicorn log level (default info)
```

The server fails fast on boot if `REDMINE_URL` is missing or not http(s).

## Authentication model

The Redmine URL is **not** user-supplied; it is fixed per deployment via
`REDMINE_URL`. This eliminates SSRF risk: clients cannot point the server at
arbitrary hosts.

The only credential a client sends is its own Redmine API key in the
`X-Redmine-API-Key` header. The server forwards it as the same header to
Redmine (so it does not land in Redmine access logs as a query string), uses
it to make one request, then discards it. There is no caching, no shared
service account, no impersonation.

## Tools

All list tools return `{items, total_count, limit, offset}` for easy paging.

### Issues

- `list_issues` (project, status, assignee, tracker, category, query, sort, include)
- `get_issue` (include: journals, attachments, relations, children, watchers)
- `create_issue` (incl. `uploads` tokens, `custom_fields`, `watcher_user_ids`)
- `update_issue` (incl. `notes`, `private_notes`)
- `add_issue_note` (thin wrapper)
- `delete_issue`

### Projects, users, memberships

- `list_projects`, `get_project`, `list_memberships`
- `list_users`, `get_user` (accepts the literal string `"current"`)

### Time entries

- `list_time_entries` (date ranges, user, project, issue)
- `create_time_entry` (issue or project, hours, activity, spent_on, comments)
- `update_time_entry`, `delete_time_entry`

### Wiki

- `list_wiki_pages`, `get_wiki_page` (with version)
- `create_or_update_wiki_page` (PUT-upsert)
- `delete_wiki_page`

### Attachments

- `get_attachment`, `download_attachment` (capped at 25 MiB, base64 out)
- `upload_attachment` (returns a token to attach via `uploads` on
  create_issue / update_issue)

### Search and metadata

- `search` (full-text across issues, news, documents, wiki, etc.)
- `list_issue_statuses`, `list_trackers`, `list_issue_categories`,
  `list_custom_fields`
- `list_issue_priorities`, `list_time_entry_activities`,
  `list_document_categories`

## Deployment

For a single Redmine instance, run one container per environment:

```sh
docker run -d --name redmine-mcp \
  --restart unless-stopped \
  -p 8080:8080 \
  -e REDMINE_URL=https://redmine.example.com \
  ghcr.io/kalvadtech/redmine-mcp:latest
```

Place it behind your usual reverse proxy and TLS termination. The MCP
protocol is HTTP-only on the server side; users get TLS via your proxy.

For multiple Redmine instances, run one container per instance with its own
`REDMINE_URL` and route by hostname / path at the proxy.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
```

The test suite is fully offline and uses `respx` to mock the Redmine HTTP
API. There are no integration tests against a live Redmine; bring-your-own.

## Contributing

Pull requests are welcome. Please:

- follow [Conventional Commits](https://www.conventionalcommits.org/),
- keep changes terse and well-scoped (one logical change per commit),
- add or update tests for any behaviour change,
- run `pytest`, `ruff`, and `mypy` clean before opening the PR.

## License

[MIT](LICENSE) (c) 2026 Kalvad.
