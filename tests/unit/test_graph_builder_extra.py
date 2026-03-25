"""Additional graph builder coverage — edge cases and branch coverage."""

from __future__ import annotations

from pathlib import Path

from tla2langgraph.models import (
    InitPredicate,
    NextRelation,
    SubAction,
    TLAModule,
    VarAssignment,
)
from tla2langgraph.parser.graph_builder import _maps_match, _unique_id, build_state_machine

FIXTURES = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# _unique_id
# ---------------------------------------------------------------------------


def test_unique_id_no_collision() -> None:
    assert _unique_id("Foo", set()) == "Foo"


def test_unique_id_collision_once() -> None:
    result = _unique_id("Foo", {"Foo"})
    assert result == "Foo_2"


def test_unique_id_collision_twice() -> None:
    result = _unique_id("Foo", {"Foo", "Foo_2"})
    assert result == "Foo_3"


# ---------------------------------------------------------------------------
# _maps_match
# ---------------------------------------------------------------------------


def test_maps_match_empty_init_returns_false() -> None:
    assert _maps_match({}, {"x": "1"}) is False


def test_maps_match_partial_match_returns_false() -> None:
    assert _maps_match({"x": "1", "y": "2"}, {"x": "1"}) is False


def test_maps_match_full_match() -> None:
    assert _maps_match({"x": "1"}, {"x": "1", "y": "2"}) is True


# ---------------------------------------------------------------------------
# build_state_machine — no init predicate
# ---------------------------------------------------------------------------


def _make_module_no_init() -> TLAModule:
    action_a = SubAction(
        name="ActionA",
        guards=(VarAssignment("s", '"idle"', False, 5),),
        effects=(VarAssignment("s", '"running"', True, 6),),
        source_line=5,
    )
    action_b = SubAction(
        name="ActionB",
        guards=(VarAssignment("s", '"running"', False, 8),),
        effects=(VarAssignment("s", '"done"', True, 9),),
        source_line=8,
    )
    return TLAModule(
        module_name="NoInit",
        variables=("s",),
        init=None,
        next=NextRelation(sub_actions=(action_a, action_b), source_line=12),
        source_file=Path("noinit.tla"),
    )


def test_build_no_init_nodes_created() -> None:
    sm = build_state_machine(_make_module_no_init())
    assert len(sm.nodes) == 2
    assert sm.initial_node_id is None


def test_build_no_init_edges_inferred() -> None:
    sm = build_state_machine(_make_module_no_init())
    assert len(sm.edges) == 1
    assert sm.edges[0].source_id == "ActionA"
    assert sm.edges[0].target_id == "ActionB"


# ---------------------------------------------------------------------------
# build_state_machine — no Next
# ---------------------------------------------------------------------------


def test_build_no_next_empty_graph() -> None:
    module = TLAModule(
        module_name="NoNext",
        variables=("x",),
        init=None,
        next=None,
        source_file=Path("nonext.tla"),
    )
    sm = build_state_machine(module)
    assert sm.nodes == []
    assert sm.edges == []


# ---------------------------------------------------------------------------
# build_state_machine — empty Init predicate with no matching guard
# ---------------------------------------------------------------------------


def test_build_init_no_guard_match() -> None:
    """Init assignments that don't match any guard → initial_node_id is None."""
    action_a = SubAction(
        name="Boom",
        guards=(VarAssignment("x", '"other"', False, 3),),
        effects=(VarAssignment("x", '"changed"', True, 4),),
        source_line=3,
    )
    module = TLAModule(
        module_name="NoMatch",
        variables=("x",),
        init=InitPredicate(
            assignments=(VarAssignment("x", '"start"', False, 1),)
        ),
        next=NextRelation(sub_actions=(action_a,), source_line=5),
        source_file=Path("nomatch.tla"),
    )
    sm = build_state_machine(module)
    assert sm.initial_node_id is None
