"""Unit tests for tla2langgraph.models."""

from pathlib import Path

import pytest

from tla2langgraph.models import (
    EdgeDeclaration,
    InitPredicate,
    LangGraphSkeleton,
    NextRelation,
    NodeFunction,
    ParseError,
    ParseErrorType,
    StateField,
    StateMachine,
    StateNode,
    SubAction,
    TLAModule,
    Transition,
    VarAssignment,
)


# ---------------------------------------------------------------------------
# VarAssignment
# ---------------------------------------------------------------------------


def test_var_assignment_fields() -> None:
    va = VarAssignment(variable="light", value="red", is_primed=False, source_line=5)
    assert va.variable == "light"
    assert va.value == "red"
    assert not va.is_primed
    assert va.source_line == 5


def test_var_assignment_primed() -> None:
    va = VarAssignment(variable="light", value="green", is_primed=True, source_line=10)
    assert va.is_primed


# ---------------------------------------------------------------------------
# ParseErrorType enum
# ---------------------------------------------------------------------------


def test_parse_error_type_values() -> None:
    assert ParseErrorType.SYNTAX_ERROR.value == "syntax_error"
    assert ParseErrorType.MISSING_INIT.value == "missing_init"
    assert ParseErrorType.MISSING_NEXT.value == "missing_next"
    assert ParseErrorType.AMBIGUOUS_NAME.value == "ambiguous_name"


def test_parse_error_str_with_location() -> None:
    err = ParseError(
        message="unexpected token",
        error_type=ParseErrorType.SYNTAX_ERROR,
        line=12,
        column=5,
    )
    assert "12" in str(err)
    assert "5" in str(err)
    assert "unexpected token" in str(err)


def test_parse_error_str_without_location() -> None:
    err = ParseError(message="no Next operator", error_type=ParseErrorType.MISSING_NEXT)
    assert "missing_next" in str(err)
    assert "no Next operator" in str(err)


# ---------------------------------------------------------------------------
# StateMachine invariant
# ---------------------------------------------------------------------------


def _make_node(node_id: str, is_initial: bool = False) -> StateNode:
    return StateNode(
        id=node_id,
        label=node_id,
        is_initial=is_initial,
        tla_source=node_id,
        source_line=1,
    )


def _make_edge(source: str, target: str) -> Transition:
    return Transition(
        source_id=source,
        target_id=target,
        label=f"x={source}",
        variable="x",
        value=source,
    )


def test_state_machine_validate_passes() -> None:
    sm = StateMachine(source_module="M")
    sm.nodes = [_make_node("A"), _make_node("B")]
    sm.edges = [_make_edge("A", "B")]
    sm.validate()  # no exception


def test_state_machine_validate_bad_source() -> None:
    sm = StateMachine(source_module="M")
    sm.nodes = [_make_node("B")]
    sm.edges = [_make_edge("A", "B")]
    with pytest.raises(ValueError, match="source"):
        sm.validate()


def test_state_machine_validate_bad_target() -> None:
    sm = StateMachine(source_module="M")
    sm.nodes = [_make_node("A")]
    sm.edges = [_make_edge("A", "B")]
    with pytest.raises(ValueError, match="target"):
        sm.validate()


def test_state_machine_empty() -> None:
    sm = StateMachine(source_module="Empty")
    sm.validate()
    assert sm.nodes == []
    assert sm.edges == []


# ---------------------------------------------------------------------------
# StateNode uniqueness (conceptual — enforced by graph builder)
# ---------------------------------------------------------------------------


def test_state_node_id_uniqueness_enforced_by_set() -> None:
    n1 = _make_node("GoGreen")
    n2 = _make_node("GoGreen")
    # frozen dataclasses with same fields are equal
    assert n1 == n2
    assert len({n1, n2}) == 1


# ---------------------------------------------------------------------------
# TLAModule
# ---------------------------------------------------------------------------


def test_tla_module_fields() -> None:
    module = TLAModule(
        module_name="TrafficLight",
        variables=("light",),
        init=None,
        next=None,
        source_file=Path("traffic_light.tla"),
    )
    assert module.module_name == "TrafficLight"
    assert "light" in module.variables
