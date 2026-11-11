"""Phase 1 async timing helper tests."""

import asyncio

import pytest

from site_dna.services.timing import timed


async def test_timed_records_elapsed_seconds() -> None:
    timings: dict[str, float] = {}

    async with timed("crawl", timings):
        await asyncio.sleep(0.02)

    assert "crawl" in timings
    assert timings["crawl"] >= 0.01


async def test_timed_records_even_when_body_raises() -> None:
    timings: dict[str, float] = {}

    with pytest.raises(RuntimeError):
        async with timed("boom", timings):
            raise RuntimeError("failure")

    assert "boom" in timings
    assert timings["boom"] >= 0.0


async def test_timed_accepts_context_with_timings_attribute() -> None:
    class Context:
        def __init__(self) -> None:
            self.timings: dict[str, float] = {}

    context = Context()

    async with timed("seo", context):
        await asyncio.sleep(0)

    assert "seo" in context.timings
