from __future__ import annotations

from typing import Any

import pytest
from starlette.testclient import TestClient

from redmine_mcp import __version__
from redmine_mcp.server import build_app

CARD_PATH = "/.well-known/mcp/server-card/mcp"
API_KEY = "1234567890abcdef1234567890abcdef12345678"
AUTH = {"Authorization": f"Bearer {API_KEY}"}
LEGACY_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"},
    },
}
MODERN_META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {},
}


@pytest.fixture
def client(monkeypatch: Any) -> TestClient:
    monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
    # Disable DNS-rebinding protection: TestClient uses the "testserver" host.
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "*")
    return TestClient(build_app())


def test_server_card_is_public(client: TestClient) -> None:
    with client:
        r = client.get(CARD_PATH)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/mcp-server-card+json"


def test_server_card_payload(client: TestClient) -> None:
    with client:
        r = client.get(CARD_PATH, headers={"Host": "mcp.example.com"})
    card = r.json()
    assert card["name"] == "com.github.kalvadtech/redmine-mcp"
    assert card["version"] == __version__
    assert card["icons"][0]["src"] == "http://mcp.example.com/favicon.png"
    remote = card["remotes"][0]
    assert remote["type"] == "streamable-http"
    assert remote["url"] == "http://mcp.example.com/mcp"
    assert "2025-11-25" in remote["supportedProtocolVersions"]
    assert "2026-07-28" in remote["supportedProtocolVersions"]
    header = remote["headers"][0]
    assert header["name"] == "Authorization"
    assert header["isRequired"] is True
    assert header["isSecret"] is True


def test_wellknown_mcp_json_serves_same_card(client: TestClient) -> None:
    with client:
        r = client.get("/.well-known/mcp.json")
    assert r.status_code == 200
    assert r.json()["name"] == "com.github.kalvadtech/redmine-mcp"


def test_server_card_cors_and_caching(client: TestClient) -> None:
    with client:
        r = client.get(CARD_PATH)
        r2 = client.get(CARD_PATH, headers={"If-None-Match": r.headers["etag"]})
    assert r.headers["access-control-allow-origin"] == "*"
    assert r.headers["cache-control"] == "public, max-age=3600"
    assert r2.status_code == 304


def test_favicons_are_public(client: TestClient) -> None:
    with client:
        ico = client.get("/favicon.ico")
        png = client.get("/favicon.png")
    assert ico.status_code == 200
    assert ico.headers["content-type"] == "image/x-icon"
    assert ico.content[:4] == b"\x00\x00\x01\x00"
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_mcp_still_requires_key(client: TestClient) -> None:
    with client:
        r = client.post("/mcp", json=LEGACY_INIT)
    assert r.status_code == 401


def test_legacy_initialize_with_modern_header(client: TestClient) -> None:
    """Dual-era clients send a modern MCP-Protocol-Version header with a legacy
    initialize body; the SDK would route it modern and 400 without the shim."""
    with client:
        r = client.post(
            "/mcp",
            json=LEGACY_INIT,
            headers={**AUTH, "MCP-Protocol-Version": "2026-07-28"},
        )
    assert r.status_code == 200
    assert r.json()["result"]["serverInfo"]["name"] == "redmine"


def test_legacy_initialize_without_header(client: TestClient) -> None:
    with client:
        r = client.post("/mcp", json=LEGACY_INIT, headers=AUTH)
    assert r.status_code == 200


def test_modern_discover_without_mirror_headers(client: TestClient) -> None:
    """Mirror headers are optional per spec; the shim injects them."""
    with client:
        r = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "server/discover",
                "params": {"_meta": MODERN_META},
            },
            headers={**AUTH, "Accept": "application/json"},
        )
    assert r.status_code == 200
    assert r.json()["result"]["supportedVersions"] == ["2026-07-28"]


def test_modern_tools_call_without_mirror_headers(client: TestClient) -> None:
    with client:
        r = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "no_such_tool", "arguments": {}, "_meta": MODERN_META},
            },
            headers={**AUTH, "Accept": "application/json"},
        )
    # Tool-not-found proves the request passed header validation.
    assert r.status_code == 200
    assert "header" not in r.json().get("error", {}).get("message", "")
