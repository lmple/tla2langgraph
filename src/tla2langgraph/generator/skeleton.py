"""LangGraph Python skeleton generator.

Converts a StateMachine + TLAModule into a LangGraphSkeleton model,
then renders it via a Jinja2 template.
"""

from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from tla2langgraph.models import (
    EdgeDeclaration,
    LangGraphSkeleton,
    NodeFunction,
    StateField,
    StateMachine,
    TLAModule,
)

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def build_skeleton(sm: StateMachine, module: TLAModule) -> LangGraphSkeleton:
    """Build a LangGraphSkeleton from a StateMachine and TLAModule.

    Args:
        sm: The state machine graph.
        module: The original parsed TLA+ module.

    Returns:
        LangGraphSkeleton ready for rendering.
    """
    state_fields = [
        StateField(
            name=_to_snake(var),
            python_type="Any",
            tla_variable=var,
        )
        for var in module.variables
    ]

    node_functions = [
        NodeFunction(
            function_name=_to_snake(node.tla_source),
            tla_action=node.tla_source,
            source_line=node.source_line,
        )
        for node in sm.nodes
    ]

    # Count outgoing edges per source to determine is_conditional
    outgoing: dict[str, int] = {}
    for edge in sm.edges:
        outgoing[edge.source_id] = outgoing.get(edge.source_id, 0) + 1

    # Map tla_source → function_name for edge declarations
    tla_to_fn = {fn.tla_action: fn.function_name for fn in node_functions}

    edge_declarations = [
        EdgeDeclaration(
            source_function=tla_to_fn.get(edge.source_id, edge.source_id),
            target_function=tla_to_fn.get(edge.target_id, edge.target_id),
            label=edge.label,
            is_conditional=outgoing.get(edge.source_id, 1) > 1,
        )
        for edge in sm.edges
    ]

    return LangGraphSkeleton(
        module_name=module.module_name,
        state_fields=state_fields,
        node_functions=node_functions,
        edge_declarations=edge_declarations,
        initial_node_id=sm.initial_node_id,
    )


def render_skeleton(skeleton: LangGraphSkeleton) -> str:
    """Render a LangGraphSkeleton to a Python source string via Jinja2.

    Args:
        skeleton: The skeleton model.

    Returns:
        Python source code as a string.
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template("skeleton.py.j2")

    # Build template context with extra fields needed by the template
    edge_context = []
    node_by_fn = {fn.function_name: fn for fn in skeleton.node_functions}

    for edge in skeleton.edge_declarations:
        edge_context.append(
            {
                "source_tla": _fn_to_tla(edge.source_function, node_by_fn),
                "target_tla": _fn_to_tla(edge.target_function, node_by_fn),
                "source_function": edge.source_function,
                "target_function": edge.target_function,
                "label": edge.label,
                "is_conditional": edge.is_conditional,
            }
        )

    return template.render(
        module_name=skeleton.module_name,
        state_fields=skeleton.state_fields,
        node_functions=skeleton.node_functions,
        edge_declarations=edge_context,
        initial_node_id=skeleton.initial_node_id,
    )


def _to_snake(name: str) -> str:
    """Convert a TLA+ action name (PascalCase or mixed) to snake_case."""
    # Insert underscore before uppercase sequences followed by lowercase
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def _fn_to_tla(fn_name: str, node_by_fn: dict[str, NodeFunction]) -> str:
    """Recover the TLA+ action name from a function name."""
    node = node_by_fn.get(fn_name)
    return node.tla_action if node else fn_name
