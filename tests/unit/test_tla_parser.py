"""Unit tests for tla2langgraph.parser.tla_parser.

Written BEFORE implementation (TDD — Red phase). All tests must fail initially.
"""

from pathlib import Path

import pytest

from tla2langgraph.models import ParseError, ParseErrorType, TLAModule, VarAssignment
from tla2langgraph.parser.tla_parser import parse_tla

FIXTURES = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Traffic light — happy path
# ---------------------------------------------------------------------------


def test_parse_traffic_light_module_name() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert module.module_name == "TrafficLight"


def test_parse_traffic_light_variables() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert "light" in module.variables


def test_parse_traffic_light_init() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert module.init is not None
    assignments = {a.variable: a.value for a in module.init.assignments}
    assert assignments.get("light") == '"red"'


def test_parse_traffic_light_next_sub_actions_count() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert module.next is not None
    assert len(module.next.sub_actions) == 3


def test_parse_traffic_light_sub_action_names() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert module.next is not None
    names = {a.name for a in module.next.sub_actions}
    assert names == {"GoGreen", "GoYellow", "GoRed"}


def test_parse_traffic_light_go_green_guards() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert module.next is not None
    go_green = next(a for a in module.next.sub_actions if a.name == "GoGreen")
    guard_map = {g.variable: g.value for g in go_green.guards}
    assert guard_map.get("light") == '"red"'


def test_parse_traffic_light_go_green_effects() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert module.next is not None
    go_green = next(a for a in module.next.sub_actions if a.name == "GoGreen")
    effect_map = {e.variable: e.value for e in go_green.effects}
    assert effect_map.get("light") == '"green"'
    assert all(e.is_primed for e in go_green.effects)


def test_parse_traffic_light_source_lines_positive() -> None:
    module = parse_tla(FIXTURES / "traffic_light.tla")
    assert module.next is not None
    for action in module.next.sub_actions:
        assert action.source_line > 0


# ---------------------------------------------------------------------------
# Simple mutex — happy path
# ---------------------------------------------------------------------------


def test_parse_mutex_sub_actions() -> None:
    module = parse_tla(FIXTURES / "simple_mutex.tla")
    assert module.next is not None
    names = {a.name for a in module.next.sub_actions}
    assert names == {"Acquire", "Release"}


# ---------------------------------------------------------------------------
# Empty next (no named sub-actions)
# ---------------------------------------------------------------------------


def test_parse_empty_next_returns_module() -> None:
    module = parse_tla(FIXTURES / "empty_next.tla")
    assert isinstance(module, TLAModule)


def test_parse_empty_next_zero_sub_actions() -> None:
    module = parse_tla(FIXTURES / "empty_next.tla")
    # empty_next.tla has no named sub-actions under Next
    if module.next is not None:
        assert len(module.next.sub_actions) == 0


# ---------------------------------------------------------------------------
# Syntax error
# ---------------------------------------------------------------------------


def test_parse_syntax_error_raises_parse_error(tmp_path: Path) -> None:
    bad_tla = tmp_path / "bad.tla"
    bad_tla.write_text("---- MODULE Bad ----\nVARIABLES x\n@@@invalid@@@\n====\n")
    with pytest.raises(ParseError) as exc_info:
        parse_tla(bad_tla)
    assert exc_info.value.error_type == ParseErrorType.SYNTAX_ERROR


def test_parse_missing_file_raises_parse_error(tmp_path: Path) -> None:
    with pytest.raises((ParseError, FileNotFoundError)):
        parse_tla(tmp_path / "nonexistent.tla")
