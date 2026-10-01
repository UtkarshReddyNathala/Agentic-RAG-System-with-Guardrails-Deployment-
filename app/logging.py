"""Helpers that attach a request ID to logs."""

from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str | None) -> None:
    """Set the ID of the current request, so its logs and traces can be linked."""
    _request_id.set(request_id)


def get_request_id() -> str | None:
    """Get the current request id, if any."""
    return _request_id.get()
