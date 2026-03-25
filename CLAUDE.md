# tla2langgraph Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-25

## Active Technologies

- Python 3.11+ + tree-sitter 0.25+, tree-sitter-tlaplus 1.5+, fastapi, uvicorn, (001-tla-to-langgraph)

## Project Structure

```text
src/tla2langgraph/
├── cli.py
├── parser/          # tree-sitter TLA+ parser + graph builder
├── server/          # FastAPI app + routes
├── generator/       # LangGraph skeleton generator + Jinja2 templates
└── web/             # Single-page UI (Cytoscape.js, CDN)

tests/
├── unit/
├── integration/
└── fixtures/        # *.tla sample specifications
```

## Commands

```bash
pytest                        # run all tests
pytest --cov=tla2langgraph --cov-fail-under=90   # with coverage gate
ruff check .                  # lint
mypy --strict src/            # type check
tla2langgraph examples/traffic_light.tla   # run the tool
```

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 001-tla-to-langgraph: Added Python 3.11+ + tree-sitter 0.25+, tree-sitter-tlaplus 1.5+, fastapi, uvicorn,

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
