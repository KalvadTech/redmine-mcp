from __future__ import annotations

from typing import Any

from ..client import get_redmine_client


def client() -> Any:
    return get_redmine_client()


def csv(values: list[str] | None) -> str | None:
    if not values:
        return None
    return ",".join(values)
