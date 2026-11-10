"""Async timing helper that records durations into a scan context."""

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator


@asynccontextmanager
async def timed(name: str, ctx: Any) -> AsyncIterator[None]:
    """Measure an async block and store its elapsed seconds in ``ctx.timings``.

    ``ctx`` may be a ``ScanContext`` (which exposes ``timings``) or a plain
    mutable mapping. The duration is recorded even when the block raises.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        target = ctx.timings if hasattr(ctx, "timings") else ctx
        target[name] = elapsed
