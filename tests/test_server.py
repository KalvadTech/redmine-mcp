from __future__ import annotations

from typing import Any

from starlette.testclient import TestClient

from redmine_mcp.server import build_app


def test_up_returns_200_without_auth(monkeypatch: Any) -> None:
    monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
    app = build_app()
    with TestClient(app) as tc:
        r = tc.get("/up")
    assert r.status_code == 200
    assert r.text == "ok"


def test_up_does_not_require_api_key_header(monkeypatch: Any) -> None:
    monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
    app = build_app()
    with TestClient(app) as tc:
        r = tc.get("/up", headers={})
    assert r.status_code == 200


def test_mcp_endpoint_still_requires_key(monkeypatch: Any) -> None:
    """/up must not relax auth on /mcp."""
    monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
    app = build_app()
    with TestClient(app) as tc:
        r = tc.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={"Accept": "application/json, text/event-stream"},
        )
    assert r.status_code == 400
    assert "X-Redmine-API-Key" in r.json()["error"]["message"]


def test_load_transport_security_unset(monkeypatch: Any) -> None:
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
    from redmine_mcp.server import _load_transport_security

    assert _load_transport_security() is None


def test_load_transport_security_wildcard(monkeypatch: Any) -> None:
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "*")
    from redmine_mcp.server import _load_transport_security

    s = _load_transport_security()
    assert s is not None and s.enable_dns_rebinding_protection is False


def test_load_transport_security_list_expands_port_wildcard(monkeypatch: Any) -> None:
    monkeypatch.setenv(
        "MCP_ALLOWED_HOSTS",
        "redmine-mcp.kalvad.xyz, mcp.example.com:8443",
    )
    from redmine_mcp.server import _load_transport_security

    s = _load_transport_security()
    assert s is not None and s.enable_dns_rebinding_protection is True
    assert s.allowed_hosts == [
        "redmine-mcp.kalvad.xyz",
        "redmine-mcp.kalvad.xyz:*",
        "mcp.example.com:8443",
    ]
