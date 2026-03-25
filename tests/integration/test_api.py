"""Integration tests for tla2langgraph HTTP API.

Written BEFORE implementation (TDD — Red phase).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from tla2langgraph.parser.graph_builder import build_state_machine
from tla2langgraph.parser.tla_parser import parse_tla
from tla2langgraph.server.app import create_app

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture()
def traffic_light_app():  # type: ignore[no-untyped-def]
    module = parse_tla(FIXTURES / "traffic_light.tla")
    sm = build_state_machine(module)
    return create_app(sm, module)


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /api/graph
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_graph_status(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        r = await client.get("/api/graph")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_graph_module_name(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    assert data["module_name"] == "TrafficLight"


@pytest.mark.asyncio
async def test_graph_node_count(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    assert len(data["nodes"]) == 3


@pytest.mark.asyncio
async def test_graph_initial_node(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    initial = next((n for n in data["nodes"] if n["is_initial"]), None)
    assert initial is not None
    assert initial["id"] == "GoGreen"


@pytest.mark.asyncio
async def test_graph_edge_count(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    assert len(data["edges"]) == 3


@pytest.mark.asyncio
async def test_graph_edge_fields(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    edge = data["edges"][0]
    assert "source_id" in edge
    assert "target_id" in edge
    assert "label" in edge


# ---------------------------------------------------------------------------
# /api/export/skeleton
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_skeleton_status(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        r = await client.get("/api/export/skeleton")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_skeleton_content_disposition(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        r = await client.get("/api/export/skeleton")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert ".py" in r.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_skeleton_valid_python(traffic_light_app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=traffic_light_app), base_url="http://test"
    ) as client:
        r = await client.get("/api/export/skeleton")
    ast.parse(r.text)  # raises SyntaxError if invalid Python
