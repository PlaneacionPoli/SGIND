"""Caché en memoria con TTL para datos derivados de Excel."""

from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_DEFAULT_TTL = 300


def cache_get(
    store: dict[Any, tuple[float, T]],
    key: Any,
    loader: Callable[[], T],
    *,
    ttl: int = _DEFAULT_TTL,
) -> T:
    now = time.time()
    entry = store.get(key)
    if entry is not None:
        value, ts = entry
        if now - ts < ttl:
            return value
    value = loader()
    store[key] = (value, now)
    return value


def cache_clear(store: dict[Any, tuple[float, Any]]) -> None:
    store.clear()
