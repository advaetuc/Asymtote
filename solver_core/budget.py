"""Optional cooperative deadline; standalone numerical calls have no time limit."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_deadline: ContextVar[float | None] = ContextVar("solver_deadline", default=None)


def check_budget() -> None:
    deadline = _deadline.get()
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("Computation deadline exceeded.")


@contextmanager
def computation_budget(seconds: float = 5.0) -> Iterator[None]:
    token = _deadline.set(time.monotonic() + seconds)
    try:
        check_budget()
        yield
        check_budget()
    finally:
        _deadline.reset(token)
