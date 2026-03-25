"""Unit tests for tla2langgraph.generator.skeleton.

Written BEFORE implementation (TDD — Red phase).
"""

from __future__ import annotations

import ast
from pathlib import Path

from tla2langgraph.generator.skeleton import build_skeleton, render_skeleton
from tla2langgraph.parser.graph_builder import build_state_machine
from tla2langgraph.parser.tla_parser import parse_tla

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _traffic_light_skeleton():  # type: ignore[no-untyped-def]
    module = parse_tla(FIXTURES / "traffic_light.tla")
    sm = build_state_machine(module)
    return build_skeleton(sm, module), render_skeleton(build_skeleton(sm, module))


# ---------------------------------------------------------------------------
# LangGraphSkeleton model
# ---------------------------------------------------------------------------


def test_skeleton_state_fields() -> None:
    skeleton, _ = _traffic_light_skeleton()
    field_names = {f.name for f in skeleton.state_fields}
    assert "light" in field_names


def test_skeleton_node_functions_count() -> None:
    skeleton, _ = _traffic_light_skeleton()
    assert len(skeleton.node_functions) == 3


def test_skeleton_node_function_names() -> None:
    skeleton, _ = _traffic_light_skeleton()
    names = {f.function_name for f in skeleton.node_functions}
    assert "go_green" in names
    assert "go_yellow" in names
    assert "go_red" in names


def test_skeleton_edge_declarations_count() -> None:
    skeleton, _ = _traffic_light_skeleton()
    assert len(skeleton.edge_declarations) == 3


def test_skeleton_initial_node_id() -> None:
    skeleton, _ = _traffic_light_skeleton()
    assert skeleton.initial_node_id == "GoGreen"


# ---------------------------------------------------------------------------
# Rendered Python output
# ---------------------------------------------------------------------------


def test_render_valid_python() -> None:
    _, rendered = _traffic_light_skeleton()
    ast.parse(rendered)  # raises SyntaxError if invalid


def test_render_contains_state_typed_dict() -> None:
    _, rendered = _traffic_light_skeleton()
    assert "class State(TypedDict)" in rendered


def test_render_contains_node_functions() -> None:
    _, rendered = _traffic_light_skeleton()
    assert "def go_green(state: State) -> State:" in rendered
    assert "def go_yellow(state: State) -> State:" in rendered
    assert "def go_red(state: State) -> State:" in rendered


def test_render_contains_add_node() -> None:
    _, rendered = _traffic_light_skeleton()
    assert 'graph.add_node("GoGreen", go_green)' in rendered


def test_render_contains_tla_comments() -> None:
    _, rendered = _traffic_light_skeleton()
    assert "TLA+ action: GoGreen" in rendered


def test_render_contains_entry_point() -> None:
    _, rendered = _traffic_light_skeleton()
    assert 'graph.set_entry_point("GoGreen")' in rendered


def test_render_contains_langgraph_imports() -> None:
    _, rendered = _traffic_light_skeleton()
    assert "from langgraph.graph import StateGraph" in rendered
    assert "TypedDict" in rendered
