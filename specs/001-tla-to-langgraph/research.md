# Research: TLA+ to LangGraph State Machine Tool

**Branch**: `001-tla-to-langgraph` | **Phase**: 0 | **Date**: 2026-03-25

## TLA+ Parsing Strategy

### Decision
Use **tree-sitter + tree-sitter-tlaplus** as the TLA+ parser.

### Rationale
- Pure Python wheels on PyPI (`tree-sitter`, `tree-sitter-tlaplus`); no JVM, no build toolchain
- Actively maintained — v1.5.0 released October 2024; used by GitHub's own TLA+ syntax highlighting
- Exposes exactly the node types needed:
  - `operator_definition` — captures `Init`, `Next`, and named sub-actions
  - `conj_list` / `conj_item` — conjunctive bullet lists (action bodies)
  - `disj_list` / `disj_item` — disjunctive bullet lists (`Next` disjuncts)
  - `prime` / `bound_postfix_op` — primed variable assignments (`var'`)
- Tree-sitter query API (S-expression patterns) allows targeting the required subset
  without traversing the full parse tree

### Alternatives Considered
- **tla2tools.jar (SANY XMLExporter)**: Most semantically correct, but requires JVM on user
  machine, ~1s JVM startup latency, and complex XML schema. Unacceptable deployment burden
  for a pip-installed CLI tool.
- **Custom recursive-descent parser**: Zero dependencies but fragile; fails on idiomatic
  TLA+ patterns (`EXTENDS`, `LET/IN`, alternative formatting). Not robust enough for v1.
- **Other Python libraries** (`PlusPy`, `tla_python`): Unmaintained or experimental;
  not suitable for production use.

---

## Frontend Graph Visualization

### Decision
Use **Cytoscape.js** (core) + **cytoscape-dagre** (layout) + **cytoscape-svg** (SVG export),
all loaded from CDN — no build step required.

### Rationale
- Single `<script>` tag inclusion from cdnjs/jsDelivr — embeds directly in a Python package's
  static HTML file
- Pan/zoom built-in (first-class API, no configuration needed)
- Click/tap events on nodes and edges built-in (`cy.on('tap', 'node', callback)`)
- **PNG export built into core**: `cy.png()` returns base64 URI or Blob — zero extra deps
- **SVG export**: `cytoscape-svg` plugin on jsDelivr; one additional `<script>` tag
- DAG/hierarchical layout via `cytoscape-dagre` plugin — appropriate for state machines
- Bundle size: ~112 KB gzipped (core); very reasonable to embed
- Actively maintained (weekly releases), MIT license

### CDN URLs
```html
<!-- Core -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.33.1/cytoscape.min.js"></script>
<!-- Dagre layout engine -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
<!-- SVG export -->
<script src="https://cdn.jsdelivr.net/npm/cytoscape-svg@0.4.0/cytoscape-svg.js"></script>
```

### Alternatives Considered
- **vis-network**: SVG export not supported (open issues since 2017). Standalone bundle is
  substantially heavier. Eliminated.
- **D3.js**: Too low-level; full interactive graph editor from D3 in a single embedded HTML
  file requires excessive hand-rolled code. Risk of fragility.
- **React Flow**: Requires React and a module bundler (Vite/webpack). Disqualified for
  no-build-step requirement.
- **dagre-d3**: Abandoned since 2017. Not recommended for new projects.
- **elkjs**: Layout engine only, not a rendering library. Would add 2–5 MB of GWT-compiled
  bundle for a single layout concern.

---

## Web Server Framework

### Decision
**FastAPI + uvicorn**

### Rationale
- Async, minimal overhead — suitable for a local single-user server
- Automatic JSON serialization for `/api/graph` endpoint
- File download response (`FileResponse` / `Response` with content-disposition) for
  Python skeleton export
- First-class support in pytest via `httpx` + `AsyncClient` for integration tests
- `webbrowser.open()` (Python stdlib) for browser launch after server startup

### Server Lifecycle
1. CLI parses TLA+ file → builds in-memory `StateMachine` object
2. FastAPI app initialized with the `StateMachine` injected as application state
3. uvicorn starts on `127.0.0.1`, random available port (bind to loopback only)
4. `webbrowser.open(f"http://127.0.0.1:{port}")` called after server ready
5. Server runs until user terminates (Ctrl+C)

---

## Code Generation

### Decision
**Jinja2 templates** for LangGraph skeleton generation

### Rationale
- Clean separation of template logic from Python code
- Easily testable (render template → assert output string)
- Handles variable numbers of nodes/edges without string concatenation complexity
- Already a transitive dependency of FastAPI; no extra install needed

---

## Python Version & Tooling

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Python version | 3.11+ | `TypedDict` inline syntax, `tomllib` stdlib, match statements |
| Linting | ruff | Fast, replaces flake8+isort+pyupgrade; single config in `pyproject.toml` |
| Type checking | mypy --strict | Constitution requirement |
| Testing | pytest + pytest-asyncio + httpx | FastAPI async testing pattern |
| Coverage | pytest-cov | Enforces ≥90% gate from constitution |
| Packaging | pyproject.toml (PEP 517) + hatchling | Modern packaging, no setup.py |
