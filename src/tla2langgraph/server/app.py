"""FastAPI application factory for tla2langgraph."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from tla2langgraph.models import StateMachine, TLAModule


def create_app(state_machine: StateMachine, tla_module: TLAModule) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        state_machine: The parsed state machine to serve.
        tla_module: The original parsed TLA+ module (for code generation).

    Returns:
        Configured FastAPI application ready to serve.
    """
    app = FastAPI(title="tla2langgraph", version="0.1.0")

    # Attach shared state
    app.state.state_machine = state_machine
    app.state.tla_module = tla_module

    # Register API routes
    from tla2langgraph.server.routes import router  # noqa: PLC0415

    app.include_router(router)

    # Serve web UI static files at root
    web_dir = Path(__file__).parent.parent / "web"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

    return app
