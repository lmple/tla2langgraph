"""CLI entry point for tla2langgraph."""

from __future__ import annotations

import socket
import webbrowser
from pathlib import Path
from threading import Timer

import typer
import uvicorn

from tla2langgraph.models import ParseError
from tla2langgraph.parser.graph_builder import build_state_machine
from tla2langgraph.parser.tla_parser import parse_tla
from tla2langgraph.server.app import create_app

app = typer.Typer(add_completion=False)


def _find_free_port(preferred: int) -> int:
    """Return a free TCP port on 127.0.0.1."""
    if preferred != 0:
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@app.command()
def main(
    spec_file: Path = typer.Argument(..., help="Path to the .tla specification file"),
    port: int = typer.Option(0, "--port", help="Port for the local web server (0 = auto)"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open the browser"),
) -> None:
    """Draw a state machine from a TLA+ spec and serve an interactive diagram."""
    # Validate file exists
    if not spec_file.exists():
        typer.echo(f"tla2langgraph: file not found: {spec_file}", err=True)
        raise typer.Exit(code=1)

    # Parse TLA+
    try:
        tla_module = parse_tla(spec_file)
    except ParseError as exc:
        if exc.line is not None and exc.column is not None:
            typer.echo(
                f"tla2langgraph: parse error at {spec_file}:{exc.line}:{exc.column}: {exc.message}",
                err=True,
            )
        else:
            typer.echo(
                f"tla2langgraph: parse error in {spec_file}: {exc.message}", err=True
            )
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"tla2langgraph: internal error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    # Build state machine
    try:
        state_machine = build_state_machine(tla_module)
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"tla2langgraph: internal error building graph: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    # Warn about edge cases
    if tla_module.init is None:
        typer.echo(
            "tla2langgraph: warning: no Init operator found; initial state not marked"
        )
    if tla_module.next is None or len(tla_module.next.sub_actions) == 0:
        typer.echo(
            "tla2langgraph: warning: no named sub-actions found under Next; "
            "diagram will be empty"
        )

    bound_port = _find_free_port(port)
    fastapi_app = create_app(state_machine, tla_module)

    typer.echo(f"tla2langgraph: serving on http://127.0.0.1:{bound_port}")

    if not no_browser:
        typer.echo("tla2langgraph: opening browser...")
        url = f"http://127.0.0.1:{bound_port}"
        Timer(0.5, lambda: webbrowser.open(url)).start()

    typer.echo("tla2langgraph: press Ctrl+C to stop")

    try:
        uvicorn.run(
            fastapi_app,
            host="127.0.0.1",
            port=bound_port,
            log_level="error",
        )
    except KeyboardInterrupt:
        typer.echo("\ntla2langgraph: stopped")
        raise typer.Exit(code=0)
