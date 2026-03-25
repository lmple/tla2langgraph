"""End-to-end integration tests: full pipeline from TLA+ fixture to API responses."""

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
def app():  # type: ignore[no-untyped-def]
    module = parse_tla(FIXTURES / "traffic_light.tla")
    sm = build_state_machine(module)
    return create_app(sm, module)


@pytest.mark.asyncio
async def test_e2e_health(app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_e2e_graph_three_nodes(app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    assert len(data["nodes"]) == 3


@pytest.mark.asyncio
async def test_e2e_graph_three_edges(app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    assert len(data["edges"]) == 3


@pytest.mark.asyncio
async def test_e2e_graph_node_names(app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        data = (await client.get("/api/graph")).json()
    names = {n["id"] for n in data["nodes"]}
    assert names == {"GoGreen", "GoYellow", "GoRed"}


@pytest.mark.asyncio
async def test_e2e_skeleton_valid_python(app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.get("/api/export/skeleton")
    ast.parse(r.text)


@pytest.mark.asyncio
async def test_e2e_skeleton_contains_actions(app) -> None:  # type: ignore[no-untyped-def]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        text = (await client.get("/api/export/skeleton")).text
    assert "GoGreen" in text
    assert "GoYellow" in text
    assert "GoRed" in text
