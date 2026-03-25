"""Build a StateMachine from a parsed TLAModule.

Edge inference: if action A sets var' = V and action B guards on var = V,
draw a directed edge A → B.
"""

from __future__ import annotations

from tla2langgraph.models import (
    StateMachine,
    StateNode,
    SubAction,
    TLAModule,
    Transition,
)


def build_state_machine(module: TLAModule) -> StateMachine:
    """Derive a StateMachine from a parsed TLAModule.

    Args:
        module: Parsed TLA+ module.

    Returns:
        StateMachine with nodes and inferred edges.
    """
    sm = StateMachine(source_module=module.module_name)

    if module.next is None or len(module.next.sub_actions) == 0:
        return sm

    # Build nodes
    seen_ids: set[str] = set()
    nodes: list[StateNode] = []
    for action in module.next.sub_actions:
        node_id = _unique_id(action.name, seen_ids)
        seen_ids.add(node_id)
        nodes.append(
            StateNode(
                id=node_id,
                label=node_id,
                is_initial=False,
                tla_source=action.name,
                source_line=action.source_line,
            )
        )

    # Mark initial node by matching Init assignments to action guards
    initial_id: str | None = None
    if module.init is not None and module.init.assignments:
        init_map = {a.variable: a.value for a in module.init.assignments}
        for action, node in zip(module.next.sub_actions, nodes):
            guard_map = {g.variable: g.value for g in action.guards}
            if _maps_match(init_map, guard_map):
                initial_id = node.id
                break

    # Rebuild nodes with is_initial flag
    sm.nodes = [
        StateNode(
            id=n.id,
            label=n.label,
            is_initial=(n.id == initial_id),
            tla_source=n.tla_source,
            source_line=n.source_line,
        )
        for n in nodes
    ]
    sm.initial_node_id = initial_id

    # Infer edges via variable-value pattern matching
    sm.edges = _infer_edges(module, sm.nodes)
    sm.validate()
    return sm


def _unique_id(name: str, seen: set[str]) -> str:
    """Return name if unique, else qualify with a counter suffix."""
    if name not in seen:
        return name
    i = 2
    while f"{name}_{i}" in seen:
        i += 1
    return f"{name}_{i}"


def _maps_match(init_map: dict[str, str], guard_map: dict[str, str]) -> bool:
    """Return True if all init assignments appear in the guard map."""
    if not init_map:
        return False
    return all(guard_map.get(var) == val for var, val in init_map.items())


def _build_var_maps(
    actions: tuple[SubAction, ...],
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Build effects map and guards map for all sub-actions."""
    effects_map = {a.name: {e.variable: e.value for e in a.effects} for a in actions}
    guards_map = {a.name: {g.variable: g.value for g in a.guards} for a in actions}
    return effects_map, guards_map


def _matching_patterns(
    src_effects: dict[str, str], tgt_guards: dict[str, str]
) -> list[str]:
    """Return label strings for variable-value pairs bridging two actions."""
    return [
        f"{var}={val}"
        for var, val in src_effects.items()
        if tgt_guards.get(var) == val
    ]


def _infer_edges(module: TLAModule, nodes: list[StateNode]) -> list[Transition]:
    """Infer directed edges by matching effects to guards across sub-actions."""
    if module.next is None:
        return []

    actions = module.next.sub_actions
    node_by_name = {n.tla_source: n for n in nodes}
    effects_map, guards_map = _build_var_maps(actions)

    edges: list[Transition] = []
    seen_pairs: set[tuple[str, str]] = set()

    for src_action in actions:
        src_node = node_by_name.get(src_action.name)
        if src_node is None:
            continue
        src_effects = effects_map[src_action.name]

        for tgt_action in actions:
            if tgt_action.name == src_action.name:
                continue
            tgt_node = node_by_name.get(tgt_action.name)
            if tgt_node is None:
                continue

            matching = _matching_patterns(src_effects, guards_map[tgt_action.name])

            if matching:
                pair = (src_node.id, tgt_node.id)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                edges.append(
                    Transition(
                        source_id=src_node.id,
                        target_id=tgt_node.id,
                        label=", ".join(matching),
                        variable=matching[0].split("=")[0],
                        value=matching[0].split("=")[1],
                    )
                )

    return edges
