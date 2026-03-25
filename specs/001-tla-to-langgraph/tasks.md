---

description: "Task list for tla2langgraph — TLA+ to LangGraph state machine tool"
---

# Tasks: TLA+ to LangGraph State Machine Tool

**Input**: Design documents from `/specs/001-tla-to-langgraph/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅, research.md ✅

**Tests**: Included — constitution Principle II mandates TDD (Red-Green-Refactor).
Write tests before implementation; confirm they fail before writing the code.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in all descriptions

## Path Conventions

All paths are relative to repository root.

---

## Phase 1: Setup

**Purpose**: Project initialization — scaffold, packaging config, test fixtures.

- [x] T001 Create `pyproject.toml` with all dependencies (tree-sitter, tree-sitter-tlaplus, fastapi, uvicorn, jinja2, typer), dev dependencies (pytest, pytest-asyncio, pytest-cov, httpx, ruff, mypy), ruff and mypy --strict config, and pytest config with `--cov=tla2langgraph --cov-fail-under=90`
- [x] T002 Create package directory skeleton: `src/tla2langgraph/__init__.py`, `src/tla2langgraph/parser/__init__.py`, `src/tla2langgraph/server/__init__.py`, `src/tla2langgraph/generator/__init__.py`, `src/tla2langgraph/generator/templates/` (empty placeholder), `src/tla2langgraph/web/` (empty placeholder)
- [x] T003 [P] Create `tests/fixtures/traffic_light.tla` — 3-state traffic light spec with `Init`, `GoGreen`, `GoYellow`, `GoRed` sub-actions and variable-value patterns linking them (matches quickstart.md example)
- [x] T004 [P] Create `tests/fixtures/simple_mutex.tla` — 2-process mutex spec with `Acquire` and `Release` sub-actions; and `tests/fixtures/empty_next.tla` — spec with `Next == SomeAction` where `SomeAction` has no named sub-actions (empty diagram edge case)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared data models and base server setup that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `src/tla2langgraph/models.py` with all dataclasses: `VarAssignment`, `InitPredicate`, `SubAction`, `NextRelation`, `TLAModule`, `StateNode`, `Transition`, `StateMachine`, `ParseErrorType` (Enum: SYNTAX_ERROR / MISSING_INIT / MISSING_NEXT / AMBIGUOUS_NAME), `ParseError`, `StateField`, `NodeFunction`, `EdgeDeclaration`, `LangGraphSkeleton` — all fields from data-model.md, using `@dataclass(frozen=True)` or `TypedDict` as appropriate
- [x] T006 [P] Write unit tests for models in `tests/unit/test_models.py`: assert field presence, `ParseErrorType` enum values, `StateMachine` invariant (all edge source/target IDs reference existing node IDs), and `StateNode` uniqueness constraint
- [x] T007 Create FastAPI app factory in `src/tla2langgraph/server/app.py`: `create_app(state_machine: StateMachine) -> FastAPI` — attach `state_machine` to `app.state`, register router from `routes.py`, serve `web/` static directory at `/`; implement `GET /api/health` returning `{"status": "ok"}`

**Checkpoint**: Foundation ready — models exist, app factory works, health endpoint responds.

---

## Phase 3: User Story 1 — Visualise State Machine (Priority: P1) 🎯 MVP

**Goal**: Load a `.tla` file via CLI → browser opens → interactive diagram with pan/zoom and click-to-inspect.

**Independent Test**: Run `tla2langgraph --no-browser tests/fixtures/traffic_light.tla`; call `GET /api/graph`; assert response contains 3 nodes (`GoGreen`, `GoYellow`, `GoRed`) and 3 directed edges inferred from `light'=X` → `light=X` patterns.

### Tests for User Story 1 ⚠️ Write these FIRST — confirm they FAIL before implementation

- [x] T008 [P] [US1] Write unit tests for TLA+ parser in `tests/unit/test_tla_parser.py`: load `traffic_light.tla` → assert `TLAModule.module_name == "TrafficLight"`, `variables == ["light"]`, `init.assignments == [VarAssignment("light","red",False,…)]`, `next.sub_actions` has 3 entries (`GoGreen`, `GoYellow`, `GoRed`), each with correct guards and effects; add syntax-error test asserting `ParseError` with line number
- [x] T009 [P] [US1] Write unit tests for graph builder in `tests/unit/test_graph_builder.py`: build `StateMachine` from `traffic_light.tla` module → assert 3 nodes, 3 edges (GoGreen→GoYellow via `light=green`, GoYellow→GoRed via `light=yellow`, GoRed→GoGreen via `light=red`), `initial_node_id == "GoGreen"`; add test for `empty_next.tla` asserting 0 nodes, 0 edges without crash
- [x] T010 [P] [US1] Write integration test for `/api/graph` in `tests/integration/test_api.py`: use `httpx.AsyncClient` with `create_app(traffic_light_state_machine)`; assert `GET /api/graph` returns 200, JSON with `nodes` list containing `{"id":"GoGreen","is_initial":true,…}` and `edges` list with correct `source_id`/`target_id`/`label` fields

### Implementation for User Story 1

- [x] T011 [P] [US1] Implement TLA+ parser in `src/tla2langgraph/parser/tla_parser.py`: use `tree_sitter` + `tree_sitter_tlaplus` to parse `.tla` bytes; extract `VARIABLES` statement → `variables`; find `Init` operator → walk conjunct list for unprimed `VarAssignment`s; find `Next` operator → collect named sub-action references in disjunct list; for each sub-action operator definition, walk conjunct list to classify primed (`var'=V`, `is_primed=True`) vs unprimed (`var=V`, `is_primed=False`) assignments; attach `source_line` from tree-sitter nodes; return `TLAModule` or raise `ParseError`
- [x] T012 [US1] Implement graph builder in `src/tla2langgraph/parser/graph_builder.py`: `build_state_machine(module: TLAModule) -> StateMachine`; create one `StateNode` per `SubAction`; infer edges by cross-matching each action's primed effects (`var'=V`) against every other action's unprimed guards (`var=V`) — same variable + same value → `Transition`; merge multi-variable matches into single edge with combined label; mark `initial_node_id` by finding the node whose guards match `Init` assignments; handle name collisions with qualified names (depends on T005, T011)
- [x] T013 [US1] Add `GET /api/graph` route to `src/tla2langgraph/server/routes.py`: serialise `app.state.state_machine` as `{"module_name":…,"nodes":[…],"edges":[…],"initial_node_id":…}` using Pydantic response model; return HTTP 500 with `{"error":"…"}` on unexpected exception (depends on T007, T012)
- [x] T014 [P] [US1] Create `src/tla2langgraph/web/index.html`: single-page UI with CDN `<script>` tags for Cytoscape.js 3.33.1, cytoscape-dagre, and cytoscape-svg; `<div id="cy">` canvas; sidebar panel `<div id="inspector">` for click-to-inspect details; toolbar placeholder with buttons `id="btn-export-skeleton"`, `id="btn-export-png"`, `id="btn-export-svg"` (buttons wired in later tasks); load `app.js`
- [x] T015 [US1] Create `src/tla2langgraph/web/app.js`: on DOMContentLoaded, `fetch('/api/graph')` → map nodes to Cytoscape elements (`{data:{id,label,is_initial}}`), edges to `{data:{source:source_id,target:target_id,label}}`; init Cytoscape with `dagre` layout (rankDir: LR) and style (initial node: double border, edge: labelled arrow); register `cy.on('tap','node')` and `cy.on('tap','edge')` to populate `#inspector` with TLA+ source name and line number (depends on T014)
- [x] T016 [US1] Configure FastAPI static file serving in `src/tla2langgraph/server/app.py`: mount `StaticFiles` from `src/tla2langgraph/web/` at `/`; ensure `GET /` returns `index.html` (depends on T007, T014)
- [x] T017 [US1] Implement CLI entry point in `src/tla2langgraph/cli.py`: typer app with `tla2langgraph(spec_file: Path, port: int = 0, no_browser: bool = False)`; validate file exists → exit 1 with stderr message if not; call `parse_tla(spec_file)` → `build_state_machine()` → `create_app()`; bind uvicorn on `127.0.0.1:{port}` (port=0 → OS assigns); print `serving on http://127.0.0.1:{port}` to stdout; call `webbrowser.open()` unless `--no-browser`; run uvicorn; catch `ParseError` → print to stderr, exit 1; catch unexpected → exit 2 (depends on T011, T012, T007, T016)

**Checkpoint**: US1 complete — `tla2langgraph traffic_light.tla` opens browser showing 3-node diagram with pan/zoom and click-to-inspect.

---

## Phase 4: User Story 2 — Export LangGraph Python Skeleton (Priority: P2)

**Goal**: Click "Export Python skeleton" in the browser → download a syntactically valid `.py` file with `StateGraph`, `State` TypedDict, stub node functions, and edges.

**Independent Test**: Load `traffic_light.tla`; call `GET /api/export/skeleton`; assert `Content-Disposition: attachment; filename="traffic_light_graph.py"`; execute the downloaded file with `python traffic_light_graph.py` and verify it runs without error (langgraph installed).

### Tests for User Story 2 ⚠️ Write these FIRST — confirm they FAIL before implementation

- [x] T018 [P] [US2] Write unit tests for skeleton generator in `tests/unit/test_skeleton.py`: build `LangGraphSkeleton` from `traffic_light` `StateMachine` → assert `state_fields` contains `StateField(name="light",…)`, `node_functions` has 3 entries with snake_case names (`go_green`, `go_yellow`, `go_red`), `edge_declarations` has 3 entries; render to string → assert contains `class State(TypedDict)`, `def go_green(state: State) -> State`, `graph.add_node("GoGreen", go_green)`, `# TLA+ action: GoGreen`, `graph.set_entry_point("GoGreen")`
- [x] T019 [P] [US2] Add integration tests for `/api/export/skeleton` in `tests/integration/test_api.py`: assert `GET /api/export/skeleton` returns 200, `Content-Type: application/octet-stream`, `Content-Disposition` header with `attachment; filename="traffic_light_graph.py"`; assert response body is valid Python (use `ast.parse()`)

### Implementation for User Story 2

- [x] T020 [US2] Create Jinja2 template `src/tla2langgraph/generator/templates/skeleton.py.j2`: emit file header comment, `from typing import Any`, `from typing_extensions import TypedDict`, `from langgraph.graph import StateGraph, END`; `class State(TypedDict):` with one field per `state_fields`; one stub function per `node_functions` with docstring referencing TLA+ action name and source line; `graph = StateGraph(State)` assembly block with `add_node` calls, `add_edge`/`add_conditional_edges` calls (use conditional edges when node has multiple outgoing edges), `set_entry_point`, `compiled = graph.compile()`
- [x] T021 [US2] Implement skeleton generator in `src/tla2langgraph/generator/skeleton.py`: `build_skeleton(sm: StateMachine, module: TLAModule) -> LangGraphSkeleton` — derive `StateField` list from `module.variables`; create `NodeFunction` per `StateNode` (snake_case name via `re.sub`); create `EdgeDeclaration` per `Transition` (set `is_conditional=True` if source node has >1 outgoing edge); `render_skeleton(skeleton: LangGraphSkeleton) -> str` — load and render `skeleton.py.j2` via Jinja2 `Environment(loader=PackageLoader)` (depends on T005, T020)
- [x] T022 [US2] Add `GET /api/export/skeleton` route in `src/tla2langgraph/server/routes.py`: call `build_skeleton(app.state.state_machine, app.state.tla_module)` → `render_skeleton()` → return `Response(content, media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{module_name}_graph.py"'})` (depends on T007, T021) — also store `tla_module` on `app.state` alongside `state_machine`
- [x] T023 [US2] Wire "Export Python skeleton" button in `src/tla2langgraph/web/app.js`: add click handler for `#btn-export-skeleton` → `fetch('/api/export/skeleton')` → create `<a>` with blob URL and `download` attribute → programmatically click → revoke URL (depends on T015, T022)

**Checkpoint**: US2 complete — browser download produces a valid, executable LangGraph skeleton matching the diagram.

---

## Phase 5: User Story 3 — Save and Share the Diagram (Priority: P3)

**Goal**: Click "Export PNG" or "Export SVG" → browser downloads a legible image of the current diagram.

**Independent Test**: In the browser with `traffic_light.tla` loaded, click "Export PNG" → file downloads; open image → 3 labelled nodes and 3 labelled edges are visible.

### Tests for User Story 3 ⚠️ Write this FIRST — confirm it FAILs before implementation

- [x] T024 [P] [US3] Write end-to-end integration test in `tests/integration/test_e2e.py`: start full server with `traffic_light.tla` via `create_app`; call `GET /api/graph` → assert 3 nodes, 3 edges; call `GET /api/export/skeleton` → assert `ast.parse()` succeeds and string contains `"GoGreen"`, `"GoYellow"`, `"GoRed"`; call `GET /api/health` → assert `{"status":"ok"}`

### Implementation for User Story 3

- [x] T025 [US3] Add `cytoscape-svg` CDN `<script>` tag to `src/tla2langgraph/web/index.html` (after cytoscape-dagre script); wire `#btn-export-png` click handler in `src/tla2langgraph/web/app.js`: call `cy.png({output:"blob",bg:"white",scale:2})` → create blob URL → trigger `<a download="diagram.png">` click → revoke URL (depends on T014, T015)
- [x] T026 [US3] Wire `#btn-export-svg` click handler in `src/tla2langgraph/web/app.js`: call `cy.svg({scale:1,full:true})` → create `Blob([svgString], {type:"image/svg+xml"})` → blob URL → trigger `<a download="diagram.svg">` click → revoke URL (depends on T025)

**Checkpoint**: US3 complete — all three export actions work independently.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, observability, performance validation, documentation.

- [x] T027 [P] Add edge-case error handling in `src/tla2langgraph/cli.py` and `src/tla2langgraph/server/routes.py`: empty `Next` (0 nodes) → serve empty graph, not error; duplicate sub-action names → qualified names (`Module!Action`); non-writable output (not applicable — browser download); missing `Init` → `initial_node_id: null` with warning to stdout
- [x] T028 [P] Add error display panel in `src/tla2langgraph/web/index.html` and `src/tla2langgraph/web/app.js`: if `fetch('/api/graph')` returns non-200 → show `#error-panel` with message; hide `#cy` canvas
- [x] T029 [P] Write performance benchmark in `tests/integration/test_benchmark.py`: parse + build graph from `traffic_light.tla` (and a generated 100-node fixture) 10 times; assert median wall time < 2 s per constitution Principle IV; use `time.perf_counter`
- [x] T030 [P] Run `ruff check src/ tests/` and `mypy --strict src/`; fix all type errors and lint warnings across all source files
- [x] T031 Update `README.md`: add project purpose, installation (`pip install tla2langgraph`), quick-start usage (matching `quickstart.md`), and link to `specs/001-tla-to-langgraph/quickstart.md` for full docs
- [x] T032 [P] Add CI smoke test in `.github/workflows/ci.yml` (or equivalent): run `tla2langgraph --no-browser tests/fixtures/traffic_light.tla &`; wait for health check `curl -sf http://127.0.0.1:PORT/api/health`; assert exit 0; validates quickstart example per constitution Principle V

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **blocks all user stories**
- **US1 (Phase 3)**: Depends on Foundational; blocks US2 (US2 reuses parser + server)
- **US2 (Phase 4)**: Depends on US1 completion (server app, TLAModule in app.state)
- **US3 (Phase 5)**: Depends on US1 completion (Cytoscape instance in app.js); independent of US2
- **Polish (Phase N)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: Parser → Graph Builder → FastAPI routes → Web UI → CLI
- **US2 (P2)**: Depends on US1 (reuses `app.state.tla_module`, `app.state.state_machine`, existing routes.py and app.js)
- **US3 (P3)**: Depends on US1 (reuses Cytoscape instance); independent of US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation begins
- Models before services (`models.py` → `tla_parser.py` → `graph_builder.py`)
- Server factory before routes (`app.py` → `routes.py`)
- Routes before frontend wiring (`routes.py` → `app.js` handler)
- Story complete and independently testable before moving to next

### Parallel Opportunities

- T003, T004 — fixture creation, parallel with each other
- T006 — model unit tests, parallel with T007
- T008, T009, T010 — US1 test writing, all parallel with each other
- T011, T014 — US1 parser and HTML, parallel with each other (different files)
- T018, T019 — US2 test writing, parallel with each other
- T024 — US3 e2e test, parallel with T023 (US2 button wiring)
- T027, T028, T029, T030, T032 — all polish tasks parallel with each other

---

## Parallel Example: User Story 1

```bash
# Write all US1 tests simultaneously (all different files):
Task: "Write unit tests for TLA+ parser in tests/unit/test_tla_parser.py" (T008)
Task: "Write unit tests for graph builder in tests/unit/test_graph_builder.py" (T009)
Task: "Write integration test for /api/graph in tests/integration/test_api.py" (T010)

# After tests fail, implement parser and HTML simultaneously (different files):
Task: "Implement TLA+ parser in src/tla2langgraph/parser/tla_parser.py" (T011)
Task: "Create web/index.html with Cytoscape CDN scripts" (T014)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup)
2. Complete Phase 2 (Foundational — models + app factory)
3. Complete Phase 3 (US1 — parser, graph builder, API, web UI, CLI)
4. **STOP and VALIDATE**: `tla2langgraph tests/fixtures/traffic_light.tla`
   - Browser opens with 3-node diagram
   - Click nodes shows TLA+ source info
   - `GET /api/health` returns `{"status":"ok"}`
5. Demo to stakeholders if ready

### Incremental Delivery

1. Setup + Foundational → scaffold ready
2. + US1 → core value delivered (visualise any TLA+ spec) — **MVP**
3. + US2 → export skeleton — reduces developer boilerplate
4. + US3 → share diagrams — enables documentation workflow
5. + Polish → production-ready (CI, benchmarks, docs)

### Parallel Team Strategy

With multiple developers after Foundational phase:
- Developer A: US1 (parser + graph builder)
- Developer B: US1 (FastAPI routes + web UI)
- Developer C: US2 tests (can write skeleton tests against data-model.md before US1 is done)

---

## Notes

- `[P]` tasks = different files, no blocking dependencies
- `[USn]` maps to user story for full traceability
- All tests MUST fail before implementation — enforce Red-Green-Refactor (constitution §II)
- Commit after each completed task or logical group
- Stop at each phase checkpoint to validate the story independently
- Tree-sitter parse tree traversal in T011 is the highest-complexity task (watch cyclomatic complexity ≤10 per constitution §I — split into helper methods if needed)
