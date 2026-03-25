"""Core data models for tla2langgraph.

Three layers:
  Parse layer  — raw TLA+ constructs extracted by tree-sitter
  Graph layer  — derived StateMachine (nodes + edges)
  Generation layer — LangGraphSkeleton ready for code emission
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# ---------------------------------------------------------------------------
# Parse layer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VarAssignment:
    """A single variable assignment or guard condition.

    Used in InitPredicate (is_primed=False), SubAction guards (is_primed=False),
    and SubAction effects (is_primed=True, var' = value).
    """

    variable: str
    value: str
    is_primed: bool
    source_line: int


@dataclass(frozen=True)
class InitPredicate:
    """Represents the Init operator body — a conjunction of assignments."""

    assignments: tuple[VarAssignment, ...]


@dataclass(frozen=True)
class SubAction:
    """A named sub-action referenced in the Next relation."""

    name: str
    guards: tuple[VarAssignment, ...]   # unprimed: var = V
    effects: tuple[VarAssignment, ...]  # primed:   var' = V
    source_line: int


@dataclass(frozen=True)
class NextRelation:
    """The Next operator — a disjunction of named sub-actions."""

    sub_actions: tuple[SubAction, ...]
    source_line: int


@dataclass(frozen=True)
class TLAModule:
    """Top-level parsed content of a .tla file."""

    module_name: str
    variables: tuple[str, ...]
    init: InitPredicate | None
    next: NextRelation | None
    source_file: Path


# ---------------------------------------------------------------------------
# Graph layer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StateNode:
    """A node in the state-machine diagram, corresponding to one TLA+ sub-action."""

    id: str           # unique; qualified as Module!Action if collision
    label: str        # display label (same as id by default)
    is_initial: bool
    tla_source: str   # original TLA+ action name
    source_line: int


@dataclass(frozen=True)
class Transition:
    """A directed edge inferred from variable-value pattern matching."""

    source_id: str
    target_id: str
    label: str    # e.g. "state=running" or "state=running, phase=active"
    variable: str
    value: str


@dataclass
class StateMachine:
    """Directed graph derived from a TLA+ module."""

    source_module: str
    nodes: list[StateNode] = field(default_factory=list)
    edges: list[Transition] = field(default_factory=list)
    initial_node_id: str | None = None

    def validate(self) -> None:
        """Assert edge invariant: all source/target IDs reference existing nodes."""
        node_ids = {n.id for n in self.nodes}
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise ValueError(
                    f"Edge source '{edge.source_id}' not in node set {node_ids}"
                )
            if edge.target_id not in node_ids:
                raise ValueError(
                    f"Edge target '{edge.target_id}' not in node set {node_ids}"
                )


# ---------------------------------------------------------------------------
# Generation layer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StateField:
    """A field in the generated State TypedDict."""

    name: str          # Python identifier (sanitised from TLA+ variable)
    python_type: str   # "Any" in v1
    tla_variable: str  # original TLA+ variable name


@dataclass(frozen=True)
class NodeFunction:
    """A stub function in the generated skeleton."""

    function_name: str   # snake_case Python identifier
    tla_action: str      # original TLA+ action name (for comment)
    source_line: int     # line in TLA+ file (for comment)


@dataclass(frozen=True)
class EdgeDeclaration:
    """A single add_edge / add_conditional_edges call."""

    source_function: str
    target_function: str
    label: str         # TLA+ pattern (for comment)
    is_conditional: bool


@dataclass
class LangGraphSkeleton:
    """In-memory representation of the Python file to generate."""

    module_name: str
    state_fields: list[StateField] = field(default_factory=list)
    node_functions: list[NodeFunction] = field(default_factory=list)
    edge_declarations: list[EdgeDeclaration] = field(default_factory=list)
    initial_node_id: str | None = None


# ---------------------------------------------------------------------------
# Parse error model
# ---------------------------------------------------------------------------


class ParseErrorType(Enum):
    SYNTAX_ERROR = "syntax_error"
    MISSING_INIT = "missing_init"
    MISSING_NEXT = "missing_next"
    AMBIGUOUS_NAME = "ambiguous_name"


@dataclass(frozen=True)
class ParseError(Exception):
    """Raised when the TLA+ file cannot be parsed or required structure is absent."""

    message: str
    error_type: ParseErrorType
    line: int | None = None
    column: int | None = None

    def __str__(self) -> str:
        if self.line is not None and self.column is not None:
            return f"{self.error_type.value} at line {self.line}:{self.column}: {self.message}"
        return f"{self.error_type.value}: {self.message}"
