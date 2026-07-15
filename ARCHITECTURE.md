# Architecture

Redmine MCP server — exposes the Redmine REST API as MCP tools via
Streamable HTTP (Starlette/uvicorn). Python, single package, stateless.

## Directory layout

```
src/redmine_mcp/
├── __init__.py          # __version__ = "0.2.6"
├── __main__.py          # CLI entry point — argparse + uvicorn.run()
├── server.py            # Composition root: build_app(), build_mcp()
├── client.py            # RedmineClient — async httpx wrapper for Redmine API
├── middleware.py         # RedmineAuthMiddleware — pure-ASGI, per-request auth
├── errors.py            # RedmineError, AuthHeaderError
├── tools/
│   ├── __init__.py      # register_all() — calls each module's register()
│   ├── _common.py       # client() helper, csv() helper
│   ├── issues.py        # list/get/create/update/delete issues + add note
│   ├── projects.py      # list/get projects
│   ├── users.py         # list/get users
│   ├── groups.py        # CRUD groups + add/remove users
│   ├── memberships.py   # CRUD memberships + add_project_member
│   ├── roles.py         # list/get roles
│   ├── versions.py      # CRUD versions
│   ├── time_entries.py  # CRUD time entries
│   ├── wiki.py          # CRUD wiki pages
│   ├── attachments.py   # get/download/upload attachments
│   ├── files.py         # list/upload project files
│   ├── relations.py     # CRUD issue relations
│   ├── news.py          # list news
│   ├── queries.py       # list saved queries
│   ├── search.py        # full-text search
│   ├── enumerations.py  # list priorities/activities/document categories
│   ├── metadata.py      # list statuses/trackers/categories/custom fields
│   ├── journals.py      # update journal notes
│   └── my_account.py    # get/update current user
tests/                   # pytest + respx (HTTP mocking), 24 files
```

## Key types and relationships

- **`RedmineClient`** (`client.py:18`) — async wrapper over `httpx.AsyncClient`.
  Provides `get_json`, `post_json`, `put_json`, `delete`, `paginate`,
  `post_octet_stream`, `get_bytes`. One instance per request. Context manager
  (`__aenter__`/`__aexit__`). Owns its own `httpx.AsyncClient`.
- **`RedmineError`** (`errors.py:6`) — raised on non-2xx Redmine responses.
  Fields: `status`, `message`, `errors: list[str]`, `body`.
- **`AuthHeaderError`** (`errors.py:28`) — raised on missing/invalid
  `X-Redmine-API-Key` header. Status 400.
- **`RedmineAuthMiddleware`** (`middleware.py:20`) — pure-ASGI middleware.
  Extracts API key → validates → creates `RedmineClient` → binds to
  `ContextVar` → awaits inner app → closes client in `finally`.
- **`_current_client: ContextVar[RedmineClient | None]`** (`client.py:233`) —
  per-request service locator. Accessed via `get_redmine_client()` /
  `set_current_client()` / `reset_current_client()`.
- **No domain models** — all data is `dict[str, Any]`. No Pydantic models,
  dataclasses, or TypedDicts. The Redmine JSON is returned as-is.

## Control flow

```
__main__.py: main()
  └─ uvicorn.run(build_app())
       └─ server.py: build_app()
            ├─ load_base_url()          # REDMINE_URL env → validated once
            ├─ build_mcp()
            │    ├─ FastMCP("redmine", stateless_http=True, json_response=True)
            │    └─ register_all(mcp)   # 19 tool modules, @mcp.tool() decorators
            └─ mcp.streamable_http_app()
                 ├─ Route("/up", _up)   # health check
                 └─ RedmineAuthMiddleware

HTTP Request (JSON-RPC)
  → RedmineAuthMiddleware.__call__()
       ├─ skip non-HTTP / health paths
       ├─ extract X-Redmine-API-Key → validate
       ├─ invalid → send JSON-RPC error (-32600, 400) → short-circuit
       ├─ valid → RedmineClient(base_url, key) → ContextVar
       └─ inner app (FastMCP streamable HTTP)
            └─ JSON-RPC dispatch → @mcp.tool() handler
                 └─ client().get_json("/issues/42.json")
                      └─ httpx → Redmine REST API
                 → return dict
            ← JSON-RPC response
  ← HTTP response (JSON)
  ← finally: reset ContextVar, close httpx client
```

## Data flow

1. **Ingress**: MCP client sends JSON-RPC over HTTP POST.
2. **Auth extraction**: Middleware reads `X-Redmine-API-Key` header, creates
   per-request `RedmineClient`.
3. **Tool dispatch**: FastMCP routes `tools/call` to the registered async function.
4. **API call**: Tool calls `client().get_json()` etc. → `httpx.Response.json()`
   → raw `dict`.
5. **Envelope unwrapping**: Tools manually extract the resource key (e.g.
   `data.get("issue", data)` for single resources, `paginate()` for lists).
6. **Pagination normalization**: `paginate()` returns uniform `{items, total_count,
   limit, offset}` regardless of resource type.
7. **Return**: Tool returns `dict[str, Any]` → FastMCP serializes to JSON-RPC
   response → Starlette sends HTTP response.
8. **Binary**: Uploads decode base64 → bytes → `application/octet-stream`.
   Downloads stream bytes → base64 string (capped at 25 MiB).

## Design decisions

### Stateless / multi-tenant
No database, no sessions, no shared secrets. Each request carries its own API
key. `REDMINE_URL` is fixed server-side (prevents SSRF). The server is
horizontally scalable — any instance can handle any request.

### Pure-ASGI middleware (not BaseHTTPMiddleware)
`Starlette`'s `BaseHTTPMiddleware` closes the client in `finally` before
streaming SSE responses finish, which breaks FastMCP's Streamable HTTP.
The pure-ASGI approach (`middleware.py:20`) ensures the client stays alive
through the entire response lifecycle.

### ContextVar for per-request state
A `ContextVar[RedmineClient | None]` acts as a service locator. Tools call
`client()` (via `_common.py`) to get the request-scoped API client. Avoids
threading the client through every function signature — critical because
FastMCP tool signatures are introspected for LLM schema generation.

### Modular tool registration
Each tool module exports `register(mcp: FastMCP) -> None`. `register_all()`
in `tools/__init__.py` calls each in deterministic order. Tools are
self-contained — adding a new resource means adding one file.

### No client-side validation
All data is `dict[str, Any]`. No Pydantic/DTO layer. The Redmine API is the
single source of truth for validation. Errors from Redmine are surfaced as
`RedmineError` with the server's own error messages.

### Fail-fast config
`REDMINE_URL` is validated at startup (`load_base_url()`). Missing or
malformed → `RuntimeError`. `MCP_ALLOWED_HOSTS` is optional. CLI flags only
for uvicorn binding (`--host`, `--port`, `--log-level`).

### Test infrastructure
- `respx` mocks httpx at the transport layer — all tests are offline.
- `build_app(transport=...)` allows injecting mock transport for integration tests.
- `conftest.py` provides `call()` helper that invokes MCP tools via
  `FastMCP.call_tool()` and unwraps `TextContent` → JSON.

## Dependencies

| Package | Usage |
|---------|-------|
| `mcp[cli]==1.28.1` | FastMCP server, `@mcp.tool()` decorator, JSON-RPC dispatch, `TransportSecuritySettings` |
| `httpx==0.28.1` | Async HTTP client for Redmine API. `RedmineClient` owns one `AsyncClient` per request |
| `starlette==1.3.1` | ASGI app, routing (`/up` health check), `PlainTextResponse` |
| `uvicorn[standard]==0.49.0` | ASGI server, launched from `__main__.py` |
| `pydantic==2.13.4` | Transitive dependency of `mcp` (not used directly) |
| `pytest`, `pytest-asyncio`, `respx` | Test framework + HTTP mocking |
| `ruff`, `mypy` | Linting + strict type checking |

## Entry points

- **`python -m redmine_mcp`** (`__main__.py`) — production. Starts uvicorn on
  the configured host/port.
- **`build_app()`** (`server.py:60`) — composition root. Used by both
  `__main__.py` and tests (with `transport=` injection).
- **`build_mcp()`** (`server.py:16`) — creates `FastMCP` instance with tools
  registered. Used by tests that need the MCP server without the HTTP layer.
- **Tests** — `pytest` with `asyncio_mode = "auto"`. Each test file uses
  `respx` to mock Redmine API responses.
=======
