from __future__ import annotations

from collections.abc import AsyncIterator
from contextvars import ContextVar
from types import TracebackType
from typing import Any

import httpx

from . import __version__ as _version
from .errors import RedmineError

_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)
_DEFAULT_PAGE_LIMIT = 25
_MAX_PAGE_LIMIT = 100


class RedmineClient:
    """Thin async wrapper over httpx for the Redmine REST API.

    One instance per request. Owns its own httpx.AsyncClient. Closes on aexit.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: httpx.Timeout = _DEFAULT_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=False,
            headers={
                "X-Redmine-API-Key": api_key,
                "Accept": "application/json",
                "User-Agent": f"redmine-mcp/{_version}",
            },
            transport=transport,
        )

    @property
    def base_url(self) -> str:
        return self._base_url

    async def __aenter__(self) -> RedmineClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._json("GET", path, params=params)

    async def post_json(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._json("POST", path, json=json, params=params)

    async def put_json(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._json("PUT", path, json=json, params=params)

    async def delete(self, path: str, params: dict[str, Any] | None = None) -> None:
        resp = await self._client.delete(path, params=_clean_params(params))
        _raise_for_status(resp)

    async def post_octet_stream(
        self,
        path: str,
        content: bytes,
        params: dict[str, Any] | None = None,
        content_type: str = "application/octet-stream",
    ) -> Any:
        resp = await self._client.post(
            path,
            content=content,
            params=_clean_params(params),
            headers={"Content-Type": content_type},
        )
        _raise_for_status(resp)
        return resp.json() if resp.content else None

    async def get_bytes(
        self,
        url: str,
        max_bytes: int,
    ) -> tuple[bytes, str]:
        """GET an absolute URL (or path) and return (content, content_type).

        Used for attachment downloads where the URL comes from the attachment
        metadata. Enforces a hard max-size cap.
        """
        async with self._client.stream("GET", url) as resp:
            _raise_for_status(resp)
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            chunks: list[bytes] = []
            received = 0
            async for chunk in resp.aiter_bytes():
                received += len(chunk)
                if received > max_bytes:
                    raise RedmineError(
                        413,
                        f"attachment exceeds max_bytes={max_bytes}",
                    )
                chunks.append(chunk)
            return b"".join(chunks), content_type

    async def paginate(
        self,
        path: str,
        items_key: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Single-page fetch returning {items, total_count, limit, offset}.

        Redmine paginates with limit/offset and returns total_count on list
        endpoints. We expose one page at a time so callers (the LLM) can
        decide whether to keep going.
        """
        page_limit = min(limit or _DEFAULT_PAGE_LIMIT, _MAX_PAGE_LIMIT)
        merged = dict(params or {})
        merged["limit"] = page_limit
        merged["offset"] = offset
        data = await self.get_json(path, params=merged)
        return {
            "items": data.get(items_key, []),
            "total_count": data.get("total_count", 0),
            "limit": data.get("limit", page_limit),
            "offset": data.get("offset", offset),
        }

    async def iter_all(
        self,
        path: str,
        items_key: str,
        params: dict[str, Any] | None = None,
        page_size: int = _MAX_PAGE_LIMIT,
    ) -> AsyncIterator[dict[str, Any]]:
        """Iterate every item across pages. Used internally where a tool
        truly needs the full set (e.g. wiki page index)."""
        offset = 0
        while True:
            page = await self.paginate(
                path, items_key, params=params, limit=page_size, offset=offset
            )
            items = page["items"]
            for item in items:
                yield item
            offset += len(items)
            if not items or offset >= page["total_count"]:
                return

    async def _json(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        resp = await self._client.request(
            method,
            path,
            json=json,
            params=_clean_params(params),
        )
        _raise_for_status(resp)
        if not resp.content:
            return None
        return resp.json()


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    return {k: v for k, v in params.items() if v is not None}


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    status = resp.status_code
    body: Any = None
    errors: list[str] = []
    message = resp.reason_phrase or "request failed"
    try:
        body = resp.json()
    except ValueError:
        body = resp.text or None
    if isinstance(body, dict):
        raw = body.get("errors")
        if isinstance(raw, list):
            errors = [str(e) for e in raw]
            message = errors[0] if errors else message
    if status == 401:
        message = "invalid Redmine API key or unauthorized"
    elif status == 403:
        message = errors[0] if errors else "forbidden"
    elif status == 404:
        message = "not found"
    raise RedmineError(status, message, errors=errors, body=body)


_current_client: ContextVar[RedmineClient | None] = ContextVar(
    "redmine_client", default=None
)


def set_current_client(client: RedmineClient | None) -> object:
    return _current_client.set(client)


def reset_current_client(token: object) -> None:
    _current_client.reset(token)  # type: ignore[arg-type]


def get_redmine_client() -> RedmineClient:
    client = _current_client.get()
    if client is None:
        raise RuntimeError(
            "no RedmineClient bound to this request; "
            "X-Redmine-URL and X-Redmine-API-Key must be set"
        )
    return client
