from __future__ import annotations

from typing import Any


class RedmineError(Exception):
    """Raised when Redmine returns a non-2xx response."""

    def __init__(
        self,
        status: int,
        message: str,
        errors: list[str] | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.errors = errors or []
        self.body = body

    def __str__(self) -> str:
        if self.errors:
            return f"Redmine {self.status}: {self.message} ({'; '.join(self.errors)})"
        return f"Redmine {self.status}: {self.message}"


class AuthHeaderError(Exception):
    """Raised when the request credentials (Authorization: Bearer or the
    legacy X-Redmine-API-Key header) are missing or invalid."""

    def __init__(self, message: str, status: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
