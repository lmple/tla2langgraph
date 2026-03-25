# Quickstart: tla2langgraph

**Branch**: `001-tla-to-langgraph` | **Date**: 2026-03-25

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
pip install tla2langgraph
```

## Usage

### 1. Prepare a TLA+ specification

Your spec must define `Init` and `Next` operators with named sub-actions. Example:

```tla
---- MODULE TrafficLight ----
VARIABLES light

Init == light = "red"

GoGreen  == /\ light = "red"    /\ light' = "green"
GoYellow == /\ light = "green"  /\ light' = "yellow"
GoRed    == /\ light = "yellow" /\ light' = "red"

Next == GoGreen \/ GoYellow \/ GoRed
====
```

Save this as `traffic_light.tla`.

### 2. Run the tool

```bash
tla2langgraph traffic_light.tla
```

Expected output:

```
tla2langgraph: serving on http://127.0.0.1:52341
tla2langgraph: opening browser...
tla2langgraph: press Ctrl+C to stop
```

Your default browser opens automatically showing the state-machine diagram.

### 3. Explore the diagram

- **Pan**: click and drag the canvas background
- **Zoom**: scroll wheel or pinch gesture
- **Inspect a node or edge**: click it to see its TLA+ source name and line number

### 4. Export the LangGraph skeleton

Click **"Export Python skeleton"** in the web UI. Your browser downloads
`traffic_light_graph.py` — a valid Python file with LangGraph boilerplate ready
for you to fill in with business logic.

### 5. Export the diagram image

Click **"Export PNG"** or **"Export SVG"** to download the diagram as an image.

### 6. Stop the server

Press `Ctrl+C` in the terminal where `tla2langgraph` is running.

---

## Options

```bash
# Fixed port (useful when you have firewall rules or scripts)
tla2langgraph --port 8421 traffic_light.tla

# Headless / no browser (e.g. for CI validation)
tla2langgraph --no-browser traffic_light.tla
```

---

## Validation (CI use)

To verify the tool parses a spec correctly without opening a browser:

```bash
tla2langgraph --no-browser my_spec.tla &
SERVER_PID=$!
sleep 2
curl -sf http://127.0.0.1:$(cat /tmp/tla2langgraph.port)/api/health
kill $SERVER_PID
```

> **Note**: The port file path is a placeholder; the actual mechanism will be
> documented once the implementation determines how the chosen port is surfaced
> to scripts (stdout, file, or env var).

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `parse error at spec.tla:N:M` | TLA+ syntax error | Fix the reported line in your spec |
| `parse error: missing Next operator` | Spec has no `Next` definition | Add a `Next` operator with named sub-actions |
| Browser does not open | `xdg-open` / browser not configured | Use `--no-browser` and open the URL manually |
| Port already in use | Another process on the port | Use `--port 0` (auto-assign) or choose a different port |
