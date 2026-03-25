# Implementation Plan: TLA+ to LangGraph State Machine Tool

**Branch**: `001-tla-to-langgraph` | **Date**: 2026-03-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-tla-to-langgraph/spec.md`

## Summary

Build a CLI tool (`tla2langgraph`) that accepts a TLA+ specification file, parses it
using tree-sitter-tlaplus to extract named sub-actions and inferred transitions, serves
an interactive Cytoscape.js diagram on `127.0.0.1` (loopback), and provides browser-download
export of a LangGraph `StateGraph` Python skeleton and diagram PNG/SVG.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: tree-sitter 0.25+, tree-sitter-tlaplus 1.5+, fastapi, uvicorn,
jinja2, typer (CLI), httpx (test client)
**Storage**: N/A — stateless; parsed graph held in process memory only
**Testing**: pytest, pytest-asyncio, pytest-cov, httpx
**Target Platform**: macOS, Linux, Windows (cross-platform CLI installed via pip)
**Project Type**: CLI tool + embedded local web service
**Performance Goals**: Parse + serve within 2 s for ≤1,000-line specs (constitution); ≤5 s
end-to-end including server start and browser open (SC-001)
**Constraints**: Server MUST bind to 127.0.0.1 only; ≤500 MB memory; no persistent storage;
no JVM dependency
**Scale/Scope**: Single-user, single-session, local machine; ≥100 nodes / 500 edges (FR-009)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Quality ✅
- ruff + mypy --strict configured in `pyproject.toml`; enforced in CI
- Modules have single responsibility: parser, graph builder, server, generator are separate
- Cyclomatic complexity target ≤10 enforced via ruff's `C901` rule
- No dead code; all public symbols used

### II. Testing Standards ✅
- TDD: test fixtures (`*.tla`) and failing tests written before implementation
- pytest-cov gate: ≥90% coverage on new code
- Integration tests: end-to-end (load TLA+ → `/api/graph` → `/api/export/skeleton`) per FR
- Red-Green-Refactor cycle enforced in task order

### III. User Experience Consistency ✅
- CLI uses kebab-case flags (`--port`, `--no-browser`)
- Exit codes: 0 (success), 1 (user error), 2 (internal error)
- Structured JSON output from API; human-readable messages to stdout/stderr
- Breaking CLI changes will require MAJOR semver bump

### IV. Performance Requirements ✅ / ⚠️ Note
- Pure parse+transform target: ≤2 s for ≤1,000-line spec (constitution Principle IV)
- SC-001 target: ≤5 s end-to-end (parse + server start + browser open) — the additional
  3 s budget covers uvicorn startup and OS browser-open latency, not parsing
- Benchmark suite will cover the parsing stage independently; server startup not benchmarked
  separately (platform-dependent, typically <1 s for uvicorn)
- Memory cap: ≤500 MB for any operation (FR-009 scale: 100 nodes / 500 edges is tiny)

### V. Documentation ✅
- `quickstart.md` generated in this plan (see `specs/001-tla-to-langgraph/quickstart.md`)
- `README.md` MUST be updated before PR merge (per constitution Principle V)
- Quickstart example (`traffic_light.tla`) MUST be tested in CI as a smoke test

## Project Structure

### Documentation (this feature)

```text
specs/001-tla-to-langgraph/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── cli-contract.md
│   └── api-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
├── tla2langgraph/
│   ├── __init__.py
│   ├── cli.py                  # typer CLI entry point; launches server + browser
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── tla_parser.py       # tree-sitter-based TLA+ parser → TLAModule
│   │   └── graph_builder.py    # TLAModule → StateMachine (edge inference)
│   ├── server/
│   │   ├── __init__.py
│   │   ├── app.py              # FastAPI app factory (takes StateMachine)
│   │   └── routes.py           # GET /api/graph, /api/export/skeleton, /api/health
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── skeleton.py         # StateMachine → LangGraphSkeleton model
│   │   └── templates/
│   │       └── skeleton.py.j2  # Jinja2 template for .py output
│   └── web/
│       ├── index.html          # Single-page UI (Cytoscape.js, CDN)
│       └── app.js              # Frontend: fetch /api/graph, render, export buttons

tests/
├── unit/
│   ├── test_tla_parser.py      # Parse TLA+ fixtures → assert TLAModule fields
│   ├── test_graph_builder.py   # TLAModule → assert StateMachine nodes/edges
│   └── test_skeleton.py        # StateMachine → assert generated .py content
├── integration/
│   ├── test_api.py             # AsyncClient: /api/graph, /api/export/skeleton, /api/health
│   └── test_e2e.py             # Full pipeline: .tla fixture → /api/graph → skeleton
└── fixtures/
    ├── traffic_light.tla       # 3 states, 3 transitions (quickstart example)
    ├── simple_mutex.tla        # 2 processes, shared variable (edge inference test)
    └── empty_next.tla          # Next with no named sub-actions (empty diagram edge case)

pyproject.toml                  # PEP 517, hatchling, ruff + mypy config, pytest config
```

**Structure Decision**: Single project — no monorepo needed. The tool is a self-contained
Python package with an embedded static web asset (`web/`). The CLI, server, parser, and
generator are cleanly separated packages under `src/tla2langgraph/`.

## Complexity Tracking

> *No constitution violations to justify — structure is within normal bounds.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Embedded web server (FastAPI) alongside CLI | Interactive diagram requires a browser runtime; no Python-native interactive graph widget with pan/zoom + PNG/SVG export exists | A CLI-only static file output (e.g., Graphviz .dot) cannot satisfy FR-003/FR-004 (interactive, click-to-inspect) |
