# Feature Specification: TLA+ to LangGraph State Machine Tool

**Feature Branch**: `001-tla-to-langgraph`
**Created**: 2026-03-25
**Status**: Draft
**Input**: User description: "Build an application that can draw a state machine from a TLA+ specification and allow to export a Langgraph Python skeleton application based on the state machine."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualize State Machine from TLA+ Spec (Priority: P1)

A developer or formal-methods engineer has a TLA+ specification file describing a
system's state machine. They want to load that file into the tool and immediately
see an interactive diagram of the states and transitions derived from it — without
needing to write any code.

**Why this priority**: Visualisation is the core value proposition. It provides
immediate feedback on whether the TLA+ spec has been parsed correctly and whether
the inferred state machine matches the designer's intent. Without it, the export
feature has no usable foundation.

**Independent Test**: Load a sample TLA+ specification; the tool displays a
diagram showing all states as labelled nodes and all transitions as directed
labelled edges. The diagram is verifiable by a human comparing it against the
original spec.

**Acceptance Scenarios**:

1. **Given** a valid TLA+ specification file, **When** the user loads it into the
   tool, **Then** a state-machine diagram appears showing all states and labelled
   transitions derived from that specification.
2. **Given** a loaded specification, **When** the user inspects a node or edge,
   **Then** the tool displays the corresponding TLA+ action or state predicate name.
3. **Given** a TLA+ file with syntax errors, **When** the user loads it,
   **Then** the tool reports the parse error with the line number and a description,
   and no diagram is shown.

---

### User Story 2 - Export LangGraph Python Skeleton (Priority: P2)

After reviewing the visualised state machine, the developer wants to export a
runnable Python skeleton that maps each state and transition to LangGraph nodes
and edges. The skeleton should compile without errors and preserve the structure
of the state machine so the developer can fill in business logic.

**Why this priority**: Export is the second core deliverable. It translates the
visual model into actionable code, saving developers the repetitive work of
manually mapping TLA+ constructs to LangGraph boilerplate.

**Independent Test**: Export a skeleton from a loaded spec; the generated file
can be opened and executed with the LangGraph library installed, and the graph
structure (nodes and edges) matches the state machine diagram shown in Story 1.

**Acceptance Scenarios**:

1. **Given** a successfully loaded and visualised TLA+ spec, **When** the user
   triggers export, **Then** a Python file is produced containing one LangGraph
   node function per state and one edge declaration per transition.
2. **Given** a generated skeleton, **When** it is executed, **Then** it runs
   without import or syntax errors and the graph can be compiled by LangGraph.
3. **Given** an export, **When** the developer inspects it, **Then** each node
   and edge is annotated with the originating TLA+ state/action name as a comment.

---

### User Story 3 - Save and Share the Diagram (Priority: P3)

A developer wants to export the state-machine diagram as an image or structured
file so they can include it in documentation or share it with colleagues who do
not have the tool installed.

**Why this priority**: Useful for documentation and collaboration but not required
to validate the core translation workflow.

**Independent Test**: Export the diagram from a loaded spec; the output file opens
correctly in a standard image viewer or diagram tool and faithfully represents
the states and transitions shown in the interactive view.

**Acceptance Scenarios**:

1. **Given** a visualised state machine, **When** the user clicks the diagram
   export button in the web UI, **Then** the browser downloads a PNG or SVG
   image file to the user's default downloads location.
2. **Given** the exported image, **When** it is opened, **Then** all state labels
   and transition labels are legible.

---

### Edge Cases

- What happens when the TLA+ specification defines no states or no transitions
  (empty/trivial spec)? The tool MUST display an empty diagram and allow export
  of a minimal skeleton rather than crashing.
- What happens when the specification file is very large (hundreds of states)?
  The diagram MUST remain usable (scrollable/zoomable) and export MUST still
  complete within the performance budget.
- What happens when two states have the same name in different modules?
  The tool MUST disambiguate them visually (e.g., using qualified names).
- What happens when the user attempts to export before a spec has been loaded?
  The tool MUST show a clear message indicating that a spec must be loaded first.
- What happens when the target export directory is not writable?
  The tool MUST report the permission error and suggest a remedy.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a TLA+ specification file path as a CLI argument
  and automatically open the interactive web UI in the user's default browser,
  served on `127.0.0.1` (loopback only) on an available localhost port.
- **FR-002**: System MUST parse the TLA+ file and extract: (a) each named
  sub-action of the top-level `Next` relation as a state node, (b) the `Init`
  predicate to identify the initial state, and (c) directed edges between
  sub-actions by matching primed variable assignments (`var' = V`) in one
  sub-action to guard conditions (`var = V`) in another. No model-checking
  (TLC) is required or invoked.
- **FR-003**: System MUST render a directed-graph diagram of the extracted state
  machine with labelled nodes (states) and labelled directed edges (transitions).
- **FR-004**: System MUST allow users to inspect any node or edge to view its
  corresponding TLA+ identifier.
- **FR-005**: System MUST provide an export button in the web UI that triggers a
  browser download of a Python file containing a LangGraph skeleton structured
  as: (a) a shared `State` typed dict, (b) one stub node function per TLA+
  sub-action accepting and returning `State`, and (c) edge declarations via
  `add_edge` / `add_conditional_edges` matching the derived transitions.
- **FR-006**: The exported Python skeleton MUST be syntactically valid and
  include comments linking each generated element to its TLA+ source.
- **FR-007**: System MUST report parse errors with location information (line
  number) and a human-readable description.
- **FR-008**: System MUST provide an export button in the web UI that triggers a
  browser download of the state-machine diagram as a PNG or SVG image.
- **FR-009**: System MUST support specifications with at least 100 states and
  500 transitions without loss of correctness.

### Key Entities

- **TLA+ Specification**: A source file written in the TLA+ language; the
  primary input artifact. Contains module declarations, state predicates, initial
  conditions, and action definitions.
- **State Machine**: The structured representation derived from the spec; a
  directed graph of states (nodes) and transitions (edges) with labels.
- **State**: A named sub-action under the TLA+ `Next` relation (e.g., `DoFoo`,
  `HandleBar`); maps to one LangGraph node function.
- **Transition**: A directed edge between two sub-action nodes, inferred when
  one sub-action's primed assignment (`var' = V`) matches another's guard
  (`var = V`); maps to a LangGraph edge declaration.
- **LangGraph Skeleton**: The generated Python file; contains a shared `State`
  typed dict, one stub node function per TLA+ sub-action, and `add_edge` /
  `add_conditional_edges` calls assembling a `StateGraph` that mirrors the
  extracted state machine.
- **Diagram Export**: An image file (PNG/SVG) capturing the visual state-machine
  diagram for documentation or sharing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from loading a TLA+ file to viewing its state-machine
  diagram in under 5 seconds for specifications with up to 100 states.
- **SC-002**: A user can export a LangGraph Python skeleton in under 3 seconds
  after the diagram has been rendered.
- **SC-003**: The generated Python skeleton is executable without modification
  (no import or syntax errors) in 100% of cases for valid input specs.
- **SC-004**: Parse errors are reported with enough detail (location + description)
  that a user can locate and fix the issue without additional tools.
- **SC-005**: 90% of users familiar with TLA+ can successfully visualise and
  export a skeleton from their first attempt without consulting documentation.

## Clarifications

### Session 2026-03-25

- Q: What is the delivery mode for v1? → A: CLI tool that launches a local web UI (served on localhost) in the browser for interactive diagram viewing, node inspection, and export triggering.
- Q: How are TLA+ states identified and enumerated? → A: Each named sub-action of the top-level `Next` action becomes a state node; the action name becomes the node label. No model-checking is performed.
- Q: How are directed edges (transitions) derived between sub-action nodes? → A: Infer from variable-value patterns — if action A sets a variable to value V (primed assignment `var' = V`) and action B guards on that same variable equalling V (`var = V`), draw a directed edge A → B.
- Q: What shape should generated LangGraph node functions take? → A: Each node is a stub function accepting and returning a shared typed `State` dict (standard `StateGraph` pattern); edges are declared via `add_edge` / `add_conditional_edges` calls.
- Q: How does the user trigger exports and where do files go? → A: Browser download — export buttons in the web UI trigger standard browser file downloads; the user chooses the save location via the browser's native download dialog. No `--output-dir` CLI argument is needed.
- Q: Which network interface should the local web server bind to? → A: `127.0.0.1` only (loopback) — the UI is inaccessible from other machines on the network.

## Assumptions

- Target users are developers or formal-methods engineers who already understand
  TLA+ and LangGraph concepts; no tutorial on either technology is in scope.
- The tool handles the TLA+ subset where the state machine is expressed as named
  sub-actions under a top-level `Next` relation and an `Init` predicate. Each
  named sub-action is treated as a state node; full PlusCal, temporal operators,
  and arbitrary state-space enumeration are out of scope for v1.
- The tool is a CLI command that parses the TLA+ file and launches a local web
  UI served exclusively on `127.0.0.1` (loopback) in the user's browser for
  interactive diagram viewing, node inspection, and browser-download-based
  export. No remote server, cloud execution, or LAN access is required or
  permitted.
- LangGraph's Python API is the sole export target; other graph frameworks
  (e.g., NetworkX, Mermaid) are out of scope for v1.
- The diagram rendering is interactive (pan/zoom) but does not need to support
  live editing of the state machine within the diagram.
- Diagram image export (Story 3) targets static formats (PNG, SVG); animated
  or interactive export formats are out of scope.
