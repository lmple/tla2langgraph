"""TLA+ specification parser using tree-sitter-tlaplus.

Extracts the Init predicate, Next sub-actions, guards, and effects
from a .tla file. No model-checking (TLC) is performed.
"""

from __future__ import annotations

import re
from collections.abc import Generator
from pathlib import Path

import tree_sitter_tlaplus as tla_lang
from tree_sitter import Language, Node, Parser

from tla2langgraph.models import (
    InitPredicate,
    NextRelation,
    ParseError,
    ParseErrorType,
    SubAction,
    TLAModule,
    VarAssignment,
)

_TLA_LANGUAGE = Language(tla_lang.language())


def parse_tla(path: Path) -> TLAModule:
    """Parse a TLA+ specification file and return a TLAModule.

    Args:
        path: Path to the .tla file.

    Returns:
        Parsed TLAModule.

    Raises:
        ParseError: If the file cannot be parsed or has syntax errors.
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"TLA+ file not found: {path}")

    source = path.read_bytes()
    parser = Parser(_TLA_LANGUAGE)
    tree = parser.parse(source)

    if tree.root_node.has_error:
        error_node = _first_error_node(tree.root_node)
        line = error_node.start_point[0] + 1 if error_node else None
        col = error_node.start_point[1] + 1 if error_node else None
        raise ParseError(
            message="TLA+ syntax error",
            error_type=ParseErrorType.SYNTAX_ERROR,
            line=line,
            column=col,
        )

    module_name = _extract_module_name(tree.root_node, source)
    variables = _extract_variables(tree.root_node, source)
    operator_defs = _collect_operator_definitions(tree.root_node, source)

    init = _build_init(operator_defs, source)
    next_rel = _build_next(operator_defs, source)

    return TLAModule(
        module_name=module_name,
        variables=tuple(variables),
        init=init,
        next=next_rel,
        source_file=path,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _first_error_node(node: Node) -> Node | None:
    """Return the first ERROR node in the tree, DFS."""
    if node.type == "ERROR":
        return node
    for child in node.children:
        result = _first_error_node(child)
        if result:
            return result
    return None


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8")


def _extract_module_name(root: Node, source: bytes) -> str:
    """Extract the module name from `---- MODULE Name ----`."""
    for child in root.children:
        if child.type == "module":
            for sub in child.children:
                if sub.type == "identifier":
                    return _node_text(sub, source)
    # Fallback: search top-level for module header
    for child in root.children:
        if child.type == "identifier":
            return _node_text(child, source)
    return "Unknown"


def _extract_variables(root: Node, source: bytes) -> list[str]:
    """Extract VARIABLES declarations."""
    variables: list[str] = []
    for node in _walk(root):
        if node.type == "variable_declaration":
            for child in node.children:
                if child.type == "identifier_ref":
                    variables.append(_node_text(child, source))
                elif child.type == "identifier":
                    variables.append(_node_text(child, source))
    return variables


def _find_op_name(node: Node, source: bytes) -> Node | None:
    """Find the name node of an operator_definition."""
    name_node = node.child_by_field_name("name")
    if name_node is None:
        for child in node.children:
            if child.type == "identifier":
                return child
    return name_node


def _find_op_body(node: Node) -> Node | None:
    """Find the body node of an operator_definition (after ==)."""
    body = node.child_by_field_name("definition")
    if body is not None:
        return body
    found_eq = False
    for child in node.children:
        if found_eq:
            return child
        if child.type == "def_eq":
            found_eq = True
    return None


def _collect_operator_definitions(
    root: Node, source: bytes
) -> dict[str, tuple[Node, int]]:
    """Collect all operator definitions by name → (body_node, line)."""
    defs: dict[str, tuple[Node, int]] = {}
    for node in _walk(root):
        if node.type != "operator_definition":
            continue
        name_node = _find_op_name(node, source)
        if name_node is None:
            continue
        body = _find_op_body(node)
        if body is not None:
            defs[_node_text(name_node, source)] = (body, name_node.start_point[0] + 1)
    return defs


def _build_init(
    operator_defs: dict[str, tuple[Node, int]], source: bytes
) -> InitPredicate | None:
    """Build InitPredicate from the Init operator definition."""
    if "Init" not in operator_defs:
        return None
    body, _ = operator_defs["Init"]
    assignments = _extract_assignments(body, source, primed=False)
    return InitPredicate(assignments=tuple(assignments))


def _build_next(
    operator_defs: dict[str, tuple[Node, int]], source: bytes
) -> NextRelation | None:
    """Build NextRelation from the Next operator definition."""
    if "Next" not in operator_defs:
        return None
    body, line = operator_defs["Next"]

    # Collect named sub-action references from the Next body
    sub_action_names = _collect_named_refs(body, source, operator_defs)

    sub_actions: list[SubAction] = []
    for action_name in sub_action_names:
        if action_name not in operator_defs:
            continue
        action_body, action_line = operator_defs[action_name]
        guards = _extract_assignments(action_body, source, primed=False)
        effects = _extract_assignments(action_body, source, primed=True)
        sub_actions.append(
            SubAction(
                name=action_name,
                guards=tuple(guards),
                effects=tuple(effects),
                source_line=action_line,
            )
        )

    return NextRelation(sub_actions=tuple(sub_actions), source_line=line)


def _collect_named_refs(
    node: Node,
    source: bytes,
    operator_defs: dict[str, tuple[Node, int]],
) -> list[str]:
    """Collect identifier references in a disjunction that are defined operators."""
    refs: list[str] = []
    for child in _walk(node):
        if child.type in ("identifier_ref", "identifier"):
            name = _node_text(child, source)
            if name in operator_defs and name not in ("Init", "Next"):
                if name not in refs:
                    refs.append(name)
    return refs


def _extract_assignments(
    node: Node, source: bytes, *, primed: bool
) -> list[VarAssignment]:
    """Extract variable assignments from a node tree.

    When primed=True: look for `var' = value` (effects).
    When primed=False: look for `var = value` (guards/init).
    """
    assignments: list[VarAssignment] = []
    _collect_assignments(node, source, primed=primed, out=assignments)
    return assignments


def _collect_assignments(
    node: Node,
    source: bytes,
    *,
    primed: bool,
    out: list[VarAssignment],
) -> None:
    """Recursively collect assignments matching the primed flag."""
    # Look for bound_infix_op with operator "=" or "="
    if node.type in ("bound_infix_op", "infix_op_expr"):
        op_node = node.child_by_field_name("operator")
        lhs = node.child_by_field_name("lhs")
        rhs = node.child_by_field_name("rhs")

        if op_node is None or lhs is None or rhs is None:
            # Try positional children for simple binary expressions
            children = [c for c in node.children if c.type not in (",",)]
            if len(children) == 3:
                lhs, op_node, rhs = children[0], children[1], children[2]

        if op_node is not None and lhs is not None and rhs is not None:
            op_text = _node_text(op_node, source).strip()
            if op_text == "=":
                is_p = _is_primed_lhs(lhs, source)
                if is_p == primed:
                    var = _extract_var_name(lhs, source)
                    val = _node_text(rhs, source).strip()
                    if var:
                        out.append(
                            VarAssignment(
                                variable=var,
                                value=val,
                                is_primed=is_p,
                                source_line=node.start_point[0] + 1,
                            )
                        )

    for child in node.children:
        _collect_assignments(child, source, primed=primed, out=out)


def _is_primed_lhs(lhs: Node, source: bytes) -> bool:
    """Check if the LHS of an assignment is a primed variable (var')."""
    text = _node_text(lhs, source)
    return "'" in text


def _extract_var_name(lhs: Node, source: bytes) -> str | None:
    """Extract the variable name from a (possibly primed) LHS node."""
    text = _node_text(lhs, source).strip().rstrip("'").strip()
    # Keep only the identifier part
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", text)
    return match.group(1) if match else None


def _walk(node: Node) -> Generator[Node, None, None]:
    """Yield all nodes in the subtree (DFS pre-order)."""
    yield node
    for child in node.children:
        yield from _walk(child)
