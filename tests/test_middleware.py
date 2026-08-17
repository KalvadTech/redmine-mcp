from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import respx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from redmine_mcp.client import get_redmine_client
from redmine_mcp.middleware import RedmineAuthMiddleware, load_base_url

GOOD_KEY = "a" * 40
BASE_URL = "https://redmine.example.com"


def _build(base_url: str = BASE_URL) -> Starlette:
    async def probe(request: Request) -> JSONResponse:
        try:
            client = get_redmine_client()
        except RuntimeError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        return JSONResponse({"base_url": client.base_url})

    app = Starlette(routes=[Route("/probe", probe)])
    app.add_middleware(RedmineAuthMiddleware, base_url=base_url)
    return app


def test_missing_credentials_401() -> None:
    with TestClient(_build()) as tc:
        r = tc.get("/probe")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert "Bearer" in r.json()["error"]["message"]


def test_short_key_rejected() -> None:
    with TestClient(_build()) as tc:
        r = tc.get("/probe", headers={"X-Redmine-API-Key": "short"})
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert "length" in r.json()["error"]["message"]


def test_whitespace_in_key_rejected() -> None:
    with TestClient(_build()) as tc:
        r = tc.get(
            "/probe",
            headers={"X-Redmine-API-Key": "x" * 10 + " " + "y" * 10},
        )
    assert r.status_code == 401
    assert "whitespace" in r.json()["error"]["message"]


def test_bearer_happy_path() -> None:
    with TestClient(_build()) as tc:
        r = tc.get("/probe", headers={"Authorization": f"Bearer {GOOD_KEY}"})
    assert r.status_code == 200
    assert r.json()["base_url"] == BASE_URL


def test_bearer_scheme_is_case_insensitive() -> None:
    with TestClient(_build()) as tc:
        r = tc.get("/probe", headers={"Authorization": f"bearer {GOOD_KEY}"})
    assert r.status_code == 200


def test_bearer_missing_token_401() -> None:
    with TestClient(_build()) as tc:
        r = tc.get("/probe", headers={"Authorization": "Bearer"})
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_wrong_scheme_401() -> None:
    with TestClient(_build()) as tc:
        r = tc.get("/probe", headers={"Authorization": f"Basic {GOOD_KEY}"})
    assert r.status_code == 401
    assert "Bearer" in r.json()["error"]["message"]


def test_bearer_short_key_rejected() -> None:
    with TestClient(_build()) as tc:
        r = tc.get("/probe", headers={"Authorization": "Bearer short"})
    assert r.status_code == 401
    assert "length" in r.json()["error"]["message"]


@respx.mock
def test_bearer_wins_over_legacy_header() -> None:
    """When both headers are present, the Bearer token is the one forwarded
    to Redmine as X-Redmine-API-Key."""
    other_key = "b" * 40
    route = respx.get(f"{BASE_URL}/users/current.json").mock(
        return_value=httpx.Response(200, json={"user": {"id": 1}})
    )

    async def probe(request: Request) -> JSONResponse:
        client = get_redmine_client()
        await client.get_json("/users/current.json")
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/probe", probe)])
    app.add_middleware(RedmineAuthMiddleware, base_url=BASE_URL)

    with TestClient(app) as tc:
        r = tc.get(
            "/probe",
            headers={
                "Authorization": f"Bearer {GOOD_KEY}",
                "X-Redmine-API-Key": other_key,
            },
        )
    assert r.status_code == 200
    assert route.calls[0].request.headers["x-redmine-api-key"] == GOOD_KEY


def test_happy_path_binds_client_to_configured_url() -> None:
    with TestClient(_build("https://redmine.kalvad.example")) as tc:
        r = tc.get("/probe", headers={"X-Redmine-API-Key": GOOD_KEY})
    assert r.status_code == 200
    assert r.json()["base_url"] == "https://redmine.kalvad.example"


def test_load_base_url_requires_env(monkeypatch: Any) -> None:
    monkeypatch.delenv("REDMINE_URL", raising=False)
    with pytest.raises(RuntimeError, match="REDMINE_URL"):
        load_base_url()


def test_load_base_url_rejects_non_http_scheme(monkeypatch: Any) -> None:
    monkeypatch.setenv("REDMINE_URL", "ftp://redmine.example.com")
    with pytest.raises(RuntimeError, match="http"):
        load_base_url()


def test_load_base_url_strips_trailing_slash(monkeypatch: Any) -> None:
    monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com/redmine/")
    assert load_base_url() == "https://redmine.example.com/redmine"


def test_load_base_url_accepts_http(monkeypatch: Any) -> None:
    monkeypatch.setenv("REDMINE_URL", "http://localhost:3000")
    assert load_base_url() == "http://localhost:3000"


def test_lifespan_passes_through() -> None:
    """Non-http scopes (lifespan, websocket) must bypass auth."""
    seen: list[str] = []

    async def downstream(scope: Any, receive: Any, send: Any) -> None:
        seen.append(scope["type"])
        if scope["type"] == "lifespan":
            msg = await receive()
            assert msg["type"] == "lifespan.startup"
            await send({"type": "lifespan.startup.complete"})
            msg = await receive()
            assert msg["type"] == "lifespan.shutdown"
            await send({"type": "lifespan.shutdown.complete"})

    app = RedmineAuthMiddleware(downstream, base_url=BASE_URL)
    with TestClient(app):
        pass
    assert "lifespan" in seen


def test_concurrent_requests_get_separate_clients() -> None:
    """Each request must bind its own RedmineClient instance to the
    ContextVar; one request must not see another's client."""
    seen: list[Any] = []

    async def probe(request: Request) -> JSONResponse:
        c = get_redmine_client()
        seen.append(c)  # keep alive: a freed client's id() can be reused
        return JSONResponse({"id": id(c)})

    app = Starlette(routes=[Route("/probe", probe)])
    app.add_middleware(RedmineAuthMiddleware, base_url=BASE_URL)

    with TestClient(app) as tc:
        a = tc.get("/probe", headers={"X-Redmine-API-Key": GOOD_KEY}).json()["id"]
        b = tc.get("/probe", headers={"X-Redmine-API-Key": GOOD_KEY}).json()["id"]
    assert a != b
    assert len(seen) == 2 and seen[0] is not seen[1]


@respx.mock
def test_client_stays_open_during_streaming_response() -> None:
    """Regression: BaseHTTPMiddleware closed the per-request client before
    the streaming body finished, breaking the SSE responses with
    'client has been closed'. The pure-ASGI middleware must keep the
    client alive through the whole response."""
    respx.get(f"{BASE_URL}/users/current.json").mock(
        return_value=httpx.Response(200, json={"user": {"id": 99, "login": "ada"}})
    )

    async def stream_endpoint(request: Request) -> StreamingResponse:
        async def body() -> AsyncIterator[bytes]:
            yield b"event: start\n\n"
            client = get_redmine_client()
            data = await client.get_json("/users/current.json")
            yield f"event: result\ndata: {data['user']['login']}\n\n".encode()

        return StreamingResponse(body(), media_type="text/event-stream")

    app = Starlette(routes=[Route("/stream", stream_endpoint)])
    app.add_middleware(RedmineAuthMiddleware, base_url=BASE_URL)

    with TestClient(app) as tc:
        r = tc.get("/stream", headers={"X-Redmine-API-Key": GOOD_KEY})
    assert r.status_code == 200
    assert b"event: result" in r.content
    assert b"data: ada" in r.content
