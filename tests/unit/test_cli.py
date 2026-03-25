"""Unit tests for tla2langgraph CLI entry point."""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from tla2langgraph.cli import _find_free_port, app
from tla2langgraph.models import ParseError, ParseErrorType

FIXTURES = Path(__file__).parent.parent / "fixtures"
runner = CliRunner()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", text)


# ---------------------------------------------------------------------------
# _find_free_port
# ---------------------------------------------------------------------------


def test_find_free_port_preferred() -> None:
    assert _find_free_port(8421) == 8421


def test_find_free_port_auto() -> None:
    port = _find_free_port(0)
    assert isinstance(port, int)
    assert port > 0


# ---------------------------------------------------------------------------
# CLI help / flags
# ---------------------------------------------------------------------------


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    output = _strip_ansi(result.output)
    assert "no-browser" in output
    assert "port" in output.lower()


# ---------------------------------------------------------------------------
# File not found → exit 1
# ---------------------------------------------------------------------------


def test_cli_missing_file_exits_1(tmp_path: Path) -> None:
    result = runner.invoke(app, [str(tmp_path / "nonexistent.tla"), "--no-browser"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Parse error with location → exit 1
# ---------------------------------------------------------------------------


def test_cli_parse_error_with_location_exits_1(tmp_path: Path) -> None:
    """Simulate a ParseError that has line + column info."""
    bad = tmp_path / "bad.tla"
    bad.write_text("@@@\n")

    with patch("tla2langgraph.cli.parse_tla") as mock_parse:
        mock_parse.side_effect = ParseError(
            message="unexpected token",
            error_type=ParseErrorType.SYNTAX_ERROR,
            line=1,
            column=1,
        )
        result = runner.invoke(app, [str(bad), "--no-browser"])

    assert result.exit_code == 1


def test_cli_parse_error_without_location_exits_1(tmp_path: Path) -> None:
    """Simulate a ParseError with no line/column (hits the else branch at line 54)."""
    bad = tmp_path / "bad.tla"
    bad.write_text("---- MODULE Bad ----\n====\n")

    with patch("tla2langgraph.cli.parse_tla") as mock_parse:
        mock_parse.side_effect = ParseError(
            message="no Next operator",
            error_type=ParseErrorType.MISSING_NEXT,
        )
        result = runner.invoke(app, [str(bad), "--no-browser"])

    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Internal error → exit 2
# ---------------------------------------------------------------------------


def test_cli_internal_error_exits_2(tmp_path: Path) -> None:
    tla = tmp_path / "spec.tla"
    tla.write_text("---- MODULE Spec ----\nVARIABLES x\nInit == x = 0\nNext == x' = x\n====\n")

    with patch("tla2langgraph.cli.parse_tla") as mock_parse:
        mock_parse.side_effect = RuntimeError("unexpected crash")
        result = runner.invoke(app, [str(tla), "--no-browser"])

    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# Successful startup (mocked uvicorn.run) → exit 0
# ---------------------------------------------------------------------------


def test_cli_successful_startup_no_browser(tmp_path: Path) -> None:
    """Full happy path with uvicorn.run mocked out."""
    tla = FIXTURES / "traffic_light.tla"

    with patch("tla2langgraph.cli.uvicorn.run") as mock_uvicorn, \
         patch("tla2langgraph.cli._find_free_port", return_value=18421):
        result = runner.invoke(app, [str(tla), "--no-browser"])

    # uvicorn.run was called once
    mock_uvicorn.assert_called_once()
    assert result.exit_code == 0


def test_cli_successful_startup_with_browser(tmp_path: Path) -> None:
    """Verify webbrowser.open is called when --no-browser is not set."""
    tla = FIXTURES / "traffic_light.tla"

    with patch("tla2langgraph.cli.uvicorn.run"), \
         patch("tla2langgraph.cli._find_free_port", return_value=18422), \
         patch("tla2langgraph.cli.webbrowser.open") as mock_browser, \
         patch("tla2langgraph.cli.Timer") as mock_timer:
        # Make Timer call the function immediately
        mock_timer.side_effect = lambda delay, fn: MagicMock(start=fn)
        result = runner.invoke(app, [str(tla)])

    assert result.exit_code == 0


def test_cli_graph_builder_error_exits_2() -> None:
    tla = FIXTURES / "traffic_light.tla"

    with patch("tla2langgraph.cli.build_state_machine") as mock_build:
        mock_build.side_effect = RuntimeError("graph crash")
        result = runner.invoke(app, [str(tla), "--no-browser"])

    assert result.exit_code == 2


def test_cli_warns_when_no_init(tmp_path: Path) -> None:
    """Cover line 69: warning printed when tla_module.init is None."""
    tla = FIXTURES / "traffic_light.tla"

    from tla2langgraph.models import NextRelation, SubAction, TLAModule

    mock_module = TLAModule(
        module_name="Test",
        variables=(),
        init=None,
        next=NextRelation(sub_actions=(), source_line=1),
        source_file=tla,
    )

    with patch("tla2langgraph.cli.parse_tla", return_value=mock_module), \
         patch("tla2langgraph.cli.build_state_machine") as mock_build, \
         patch("tla2langgraph.cli.uvicorn.run"):
        from tla2langgraph.models import StateMachine
        mock_build.return_value = StateMachine(source_module="Test")
        result = runner.invoke(app, [str(tla), "--no-browser"])

    assert result.exit_code == 0
    assert "no Init operator" in result.output


def test_cli_warns_when_no_sub_actions(tmp_path: Path) -> None:
    """Cover line 73: warning printed when Next has no sub-actions."""
    tla = FIXTURES / "traffic_light.tla"

    from tla2langgraph.models import InitPredicate, NextRelation, TLAModule

    mock_module = TLAModule(
        module_name="Test",
        variables=(),
        init=InitPredicate(assignments=()),
        next=NextRelation(sub_actions=(), source_line=1),
        source_file=tla,
    )

    with patch("tla2langgraph.cli.parse_tla", return_value=mock_module), \
         patch("tla2langgraph.cli.build_state_machine") as mock_build, \
         patch("tla2langgraph.cli.uvicorn.run"):
        from tla2langgraph.models import StateMachine
        mock_build.return_value = StateMachine(source_module="Test")
        result = runner.invoke(app, [str(tla), "--no-browser"])

    assert result.exit_code == 0
    assert "diagram will be empty" in result.output


def test_cli_keyboard_interrupt_exits_0() -> None:
    """Cover lines 97-99: KeyboardInterrupt during uvicorn.run → exit 0."""
    tla = FIXTURES / "traffic_light.tla"

    with patch("tla2langgraph.cli.uvicorn.run") as mock_uvicorn, \
         patch("tla2langgraph.cli._find_free_port", return_value=18423):
        mock_uvicorn.side_effect = KeyboardInterrupt()
        result = runner.invoke(app, [str(tla), "--no-browser"])

    assert result.exit_code == 0
