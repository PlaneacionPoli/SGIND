"""Helper para liberar el event loop durante trabajo síncrono de pandas —
ver docs/migration/PLAN_MIGRACION_PRIORIZADO.md. El patrón ya se usaba en
main.py::_warm_caches (asyncio.to_thread); este helper lo hace reutilizable
desde cada endpoint sin repetir el `await asyncio.to_thread(...)` inline."""

import asyncio
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


async def run_sync(fn: Callable[..., T], *args: object, **kwargs: object) -> T:
    return await asyncio.to_thread(fn, *args, **kwargs)
