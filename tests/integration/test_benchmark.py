"""Performance benchmark: parse + build graph must complete within 2 s (constitution §IV)."""

from __future__ import annotations

import time
from pathlib import Path

from tla2langgraph.parser.graph_builder import build_state_machine
from tla2langgraph.parser.tla_parser import parse_tla

FIXTURES = Path(__file__).parent.parent / "fixtures"
ITERATIONS = 10
MAX_MEDIAN_SECONDS = 2.0


def _median(times: list[float]) -> float:
    sorted_times = sorted(times)
    mid = len(sorted_times) // 2
    if len(sorted_times) % 2 == 0:
        return (sorted_times[mid - 1] + sorted_times[mid]) / 2
    return sorted_times[mid]


def test_parse_and_build_within_2s_traffic_light() -> None:
    times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        module = parse_tla(FIXTURES / "traffic_light.tla")
        build_state_machine(module)
        times.append(time.perf_counter() - start)

    median = _median(times)
    assert median < MAX_MEDIAN_SECONDS, (
        f"Median parse+build time {median:.3f}s exceeds {MAX_MEDIAN_SECONDS}s limit"
    )


def test_parse_and_build_within_2s_mutex() -> None:
    times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        module = parse_tla(FIXTURES / "simple_mutex.tla")
        build_state_machine(module)
        times.append(time.perf_counter() - start)

    median = _median(times)
    assert median < MAX_MEDIAN_SECONDS, (
        f"Median parse+build time {median:.3f}s exceeds {MAX_MEDIAN_SECONDS}s limit"
    )
