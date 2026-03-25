# Data Model: TLA+ to LangGraph State Machine Tool

**Branch**: `001-tla-to-langgraph` | **Phase**: 1 | **Date**: 2026-03-25

## Overview

The tool's data model has three layers:
1. **Parse layer** — raw TLA+ constructs extracted by tree-sitter
2. **Graph layer** — the derived `StateMachine` (nodes + edges)
3. **Generation layer** — the `LangGraphSkeleton` ready for code emission

---

## Parse Layer

### `TLAModule`
Represents the top-level parsed content of a `.tla` file.

| Field | Type | Description |
|-------|------|-------------|
| `module_name` | `str` | The TLA+ module name (from `---- MODULE name ----`) |
| `variables` | `list[str]` | Variables declared by `VARIABLES` statement |
| `init` | `InitPredicate \| None` | Parsed `Init` operator definition |
| `next` | `NextRelation \| None` | Parsed `Next` operator definition |
| `source_file` | `Path` | Absolute path to the source `.tla` file |

**Validation rules:**
- `module_name` MUST be non-empty
- If `init` is `None`, graph layer emits a warning (no initial state can be marked)
- If `next` is `None`, graph layer produces an empty node list

---

### `InitPredicate`
Represents the `Init` operator body — a conjunction of variable assignments.

| Field | Type | Description |
|-------|------|-------------|
| `assignments` | `list[VarAssignment]` | Each `var = value` conjunct in `Init` |

---

### `VarAssignment`
A single variable assignment, used in both `Init` (plain) and sub-action effects (primed).

| Field | Type | Description |
|-------|------|-------------|
| `variable` | `str` | Variable name |
| `value` | `str` | Assigned value (literal string as it appears in TLA+) |
| `is_primed` | `bool` | `True` for `var' = V` (effect), `False` for `var = V` (guard/init) |
| `source_line` | `int` | Line number in source file (for error reporting) |

---

### `NextRelation`
Represents the `Next` operator — a disjunction of named sub-actions.

| Field | Type | Description |
|-------|------|-------------|
| `sub_actions` | `list[SubAction]` | Each disjunct of `Next` that resolves to a named operator |
| `source_line` | `int` | Line number of the `Next` definition |

---

### `SubAction`
A single named sub-action referenced in `Next`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Action name (e.g., `DoFoo`, `HandleBar`) |
| `guards` | `list[VarAssignment]` | Conditions on unprimed variables (`var = V`) |
| `effects` | `list[VarAssignment]` | Primed variable assignments (`var' = V`) |
| `source_line` | `int` | Line number of this action's definition |

**Constraint**: `name` MUST be unique within a module. If two sub-actions share a name
(e.g., from different imported modules), both MUST be retained with a qualified name
(`ModuleName!ActionName`).

---

## Graph Layer

### `StateMachine`
The directed graph derived from the parsed TLA+ module. This is the central
in-memory representation passed to both the web server and the code generator.

| Field | Type | Description |
|-------|------|-------------|
| `source_module` | `str` | Name of the originating TLA+ module |
| `nodes` | `list[StateNode]` | One node per named sub-action of `Next` |
| `edges` | `list[Transition]` | Inferred directed edges between nodes |
| `initial_node_id` | `str \| None` | ID of the node whose guards match `Init` assignments |

**Invariant**: Every `Transition.source_id` and `Transition.target_id` MUST reference
an existing `StateNode.id` in `nodes`.

---

### `StateNode`
A node in the state machine diagram, corresponding to one TLA+ sub-action.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Stable unique identifier (action name, or qualified if ambiguous) |
| `label` | `str` | Display label in the diagram (same as `id` by default) |
| `is_initial` | `bool` | `True` if this node's guards match the `Init` assignments |
| `tla_source` | `str` | Original TLA+ action name for traceability |
| `source_line` | `int` | Line number in source file |

**Identity rule**: `id` MUST be unique across all nodes. If a plain action name collides
(same name in different modules), qualify it as `ModuleName!ActionName`.

---

### `Transition`
A directed edge inferred from variable-value pattern matching between two sub-actions.

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | `str` | ID of the source `StateNode` (action that produces the value) |
| `target_id` | `str` | ID of the target `StateNode` (action that guards on that value) |
| `label` | `str` | Human-readable edge label, e.g., `state=running` |
| `variable` | `str` | The TLA+ variable whose value connects the two actions |
| `value` | `str` | The value bridging source effect and target guard |

**Inference rule**: An edge `A → B` is created when:
- Sub-action `A` contains an effect `var' = V`
- Sub-action `B` contains a guard `var = V`
- `A` ≠ `B`

Multiple variable-value matches between the same pair of actions produce a single edge
with a combined label (e.g., `state=running, phase=active`).

---

## Generation Layer

### `LangGraphSkeleton`
The in-memory representation of the Python file to be generated and downloaded.

| Field | Type | Description |
|-------|------|-------------|
| `module_name` | `str` | Used as the Python module/class name (sanitised to valid identifier) |
| `state_fields` | `list[StateField]` | Fields of the shared `State` TypedDict |
| `node_functions` | `list[NodeFunction]` | One per `StateNode` |
| `edge_declarations` | `list[EdgeDeclaration]` | One per `Transition` |
| `initial_node_id` | `str \| None` | Entry point for `graph.set_entry_point()` |

---

### `StateField`
A field in the generated `State` TypedDict, derived from TLA+ variables.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Python identifier (sanitised from TLA+ variable name) |
| `python_type` | `str` | Always `Any` in v1 (types are not inferred from TLA+) |
| `tla_variable` | `str` | Original TLA+ variable name (used in code comment) |

---

### `NodeFunction`
A stub function in the generated skeleton corresponding to one `StateNode`.

| Field | Type | Description |
|-------|------|-------------|
| `function_name` | `str` | Python identifier (snake_case of action name) |
| `tla_action` | `str` | Original TLA+ action name (in docstring/comment) |
| `source_line` | `int` | Line in original TLA+ file (in comment) |

Generated shape:
```python
def do_foo(state: State) -> State:
    # TLA+ action: DoFoo (spec.tla:42)
    # TODO: implement business logic
    return state
```

---

### `EdgeDeclaration`
A single `add_edge` or `add_conditional_edges` call in the generated skeleton.

| Field | Type | Description |
|-------|------|-------------|
| `source_function` | `str` | Python function name of the source node |
| `target_function` | `str` | Python function name of the target node |
| `label` | `str` | TLA+ pattern that produced this edge (in comment) |
| `is_conditional` | `bool` | `True` if source node has multiple outgoing edges |

---

## Entity Relationships

```text
TLAModule
  ├── InitPredicate
  │     └── list[VarAssignment]
  └── NextRelation
        └── list[SubAction]
              ├── guards: list[VarAssignment]
              └── effects: list[VarAssignment]

StateMachine   (derived from TLAModule)
  ├── list[StateNode]
  └── list[Transition]

LangGraphSkeleton   (derived from StateMachine + TLAModule)
  ├── list[StateField]     ← from TLAModule.variables
  ├── list[NodeFunction]   ← from StateMachine.nodes
  └── list[EdgeDeclaration] ← from StateMachine.edges
```

---

## Parse Error Model

### `ParseError`
Returned when the TLA+ file cannot be parsed or the required structure is not found.

| Field | Type | Description |
|-------|------|-------------|
| `message` | `str` | Human-readable description of the error |
| `line` | `int \| None` | Line number in source file (None if not locatable) |
| `column` | `int \| None` | Column number in source file (None if not locatable) |
| `error_type` | `ParseErrorType` | Enum: `SYNTAX_ERROR`, `MISSING_INIT`, `MISSING_NEXT`, `AMBIGUOUS_NAME` |

**Exit code mapping**:
- `SYNTAX_ERROR` → exit code 1 (user error)
- All others → exit code 1 (user error)
- Unexpected exceptions → exit code 2 (internal error)
