"""API routes for tla2langgraph web server."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter()


@router.get("/api/health")
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}


@router.get("/api/graph")
async def get_graph(request: Request) -> dict[str, object]:
    """Return the parsed state machine as a Cytoscape.js-compatible JSON graph."""
    sm = request.app.state.state_machine

    nodes = [
        {
            "id": n.id,
            "label": n.label,
            "is_initial": n.is_initial,
            "tla_source": n.tla_source,
            "source_line": n.source_line,
        }
        for n in sm.nodes
    ]

    edges = [
        {
            "source_id": e.source_id,
            "target_id": e.target_id,
            "label": e.label,
            "variable": e.variable,
            "value": e.value,
        }
        for e in sm.edges
    ]

    return {
        "module_name": sm.source_module,
        "nodes": nodes,
        "edges": edges,
        "initial_node_id": sm.initial_node_id,
    }


@router.get("/api/export/skeleton")
async def export_skeleton(request: Request) -> Response:
    """Return the generated LangGraph Python skeleton as a browser download."""
    from tla2langgraph.generator.skeleton import build_skeleton, render_skeleton  # noqa: PLC0415

    sm = request.app.state.state_machine
    module = request.app.state.tla_module

    skeleton = build_skeleton(sm, module)
    content = render_skeleton(skeleton)

    filename = f"{module.module_name.lower()}_graph.py"
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
