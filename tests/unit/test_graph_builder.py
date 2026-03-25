"""Unit tests for tla2langgraph.parser.graph_builder.

Written BEFORE implementation (TDD — Red phase). All tests must fail initially.
"""

from pathlib import Path

from tla2langgraph.models import StateMachine
from tla2langgraph.parser.graph_builder import build_state_machine
from tla2langgraph.parser.tla_parser import parse_tla

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load(name: str) -> StateMachine:
    module = parse_tla(FIXTURES / name)
    return build_state_machine(module)


# ---------------------------------------------------------------------------
# Traffic light
# ---------------------------------------------------------------------------


def test_traffic_light_node_count() -> None:
    sm = _load("traffic_light.tla")
    assert len(sm.nodes) == 3


def test_traffic_light_node_ids() -> None:
    sm = _load("traffic_light.tla")
    ids = {n.id for n in sm.nodes}
    assert ids == {"GoGreen", "GoYellow", "GoRed"}


def test_traffic_light_initial_node() -> None:
    sm = _load("traffic_light.tla")
    assert sm.initial_node_id == "GoGreen"


def test_traffic_light_edge_count() -> None:
    sm = _load("traffic_light.tla")
    assert len(sm.edges) == 3


def test_traffic_light_edges_go_green_to_yellow() -> None:
    sm = _load("traffic_light.tla")
    edge = next(
        (e for e in sm.edges if e.source_id == "GoGreen" and e.target_id == "GoYellow"),
        None,
    )
    assert edge is not None, "Expected edge GoGreen → GoYellow"
    assert "green" in edge.label


def test_traffic_light_edges_go_yellow_to_red() -> None:
    sm = _load("traffic_light.tla")
    edge = next(
        (e for e in sm.edges if e.source_id == "GoYellow" and e.target_id == "GoRed"),
        None,
    )
    assert edge is not None, "Expected edge GoYellow → GoRed"


def test_traffic_light_edges_go_red_to_green() -> None:
    sm = _load("traffic_light.tla")
    edge = next(
        (e for e in sm.edges if e.source_id == "GoRed" and e.target_id == "GoGreen"),
        None,
    )
    assert edge is not None, "Expected edge GoRed → GoGreen"


def test_traffic_light_validate_passes() -> None:
    sm = _load("traffic_light.tla")
    sm.validate()  # must not raise


# ---------------------------------------------------------------------------
# Simple mutex
# ---------------------------------------------------------------------------


def test_mutex_node_count() -> None:
    sm = _load("simple_mutex.tla")
    assert len(sm.nodes) == 2


def test_mutex_edges() -> None:
    sm = _load("simple_mutex.tla")
    assert len(sm.edges) == 2
    source_ids = {e.source_id for e in sm.edges}
    assert "Acquire" in source_ids
    assert "Release" in source_ids


# ---------------------------------------------------------------------------
# Empty next — no crash, empty graph
# ---------------------------------------------------------------------------


def test_empty_next_no_crash() -> None:
    sm = _load("empty_next.tla")
    assert isinstance(sm, StateMachine)


def test_empty_next_zero_nodes() -> None:
    sm = _load("empty_next.tla")
    assert len(sm.nodes) == 0


def test_empty_next_zero_edges() -> None:
    sm = _load("empty_next.tla")
    assert len(sm.edges) == 0


def test_empty_next_validate_passes() -> None:
    sm = _load("empty_next.tla")
    sm.validate()
