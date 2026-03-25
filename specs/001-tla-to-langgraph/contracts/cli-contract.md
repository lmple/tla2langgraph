# CLI Contract: tla2langgraph

**Branch**: `001-tla-to-langgraph` | **Date**: 2026-03-25

## Command

```
tla2langgraph [OPTIONS] SPEC_FILE
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `SPEC_FILE` | Yes | Path to the `.tla` specification file to load |

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--port INTEGER` | `0` (random available) | Port to bind the local web server on `127.0.0.1`. `0` means auto-assign. |
| `--no-browser` | `False` | Start the server without opening the browser (useful for scripting) |
| `--version` | — | Print version and exit |
| `--help` | — | Show help message and exit |

### Examples

```bash
# Standard usage — parse spec and open browser
tla2langgraph examples/traffic_light.tla

# Use a fixed port
tla2langgraph --port 8421 examples/traffic_light.tla

# CI / headless mode — start server but do not open browser
tla2langgraph --no-browser examples/traffic_light.tla
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Server started successfully (or `--version`/`--help` printed) |
| `1` | User error: file not found, TLA+ parse error, invalid arguments |
| `2` | Internal/unexpected error |

---

## Standard Output

On successful startup, the tool prints to stdout:

```
tla2langgraph: serving on http://127.0.0.1:{PORT}
tla2langgraph: opening browser...
tla2langgraph: press Ctrl+C to stop
```

When `--no-browser` is used, the second line is omitted.

## Standard Error

Parse errors are printed to stderr in the format:

```
tla2langgraph: parse error at {FILE}:{LINE}:{COL}: {MESSAGE}
```

If line/column are not available:

```
tla2langgraph: parse error in {FILE}: {MESSAGE}
```

Internal errors:

```
tla2langgraph: internal error: {MESSAGE}
```
