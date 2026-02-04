from __future__ import annotations

import time
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


def retry(
    func: Callable[[], T],
    *,
    attempts: int = 3,
    delay: float = 0.2,
    retry_on: Iterable[type[BaseException]] = (Exception,),
) -> T:
    """Retry a callable for transient failures."""

    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            return func()
        except tuple(retry_on) as exc:  # pragma: no cover - depends on caller
            last_exc = exc
            if attempt < attempts - 1:
                time.sleep(delay)
    assert last_exc is not None
    raise last_exc
