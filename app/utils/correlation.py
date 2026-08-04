import uuid
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def new_correlation_id() -> str:
    return uuid.uuid4().hex[:12]
