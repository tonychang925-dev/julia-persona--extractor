from __future__ import annotations

from typing import Any


def compile_composition(
    *,
    applicability: list[dict[str, Any]],
    reasoning_frame: dict[str, Any],
) -> dict[str, Any]:
    active = [row["chain_id"] for row in applicability if row["state"] in {"APPLIES", "PARTIALLY_APPLIES"}]
    relations = [
        relation
        for relation in reasoning_frame.get("cross_chain_relations", [])
        if relation["chain_a"] in active and relation["chain_b"] in active
    ]
    if len(active) < 2 or not relations:
        state, rule = "NONE", "MC-01"
        triggers = [f"active_chain_ids={active}", f"active_relations={len(relations)}"]
    elif any(relation["materially_competing"] for relation in relations):
        state, rule = "MATERIAL_CONFLICT", "MC-04"
        triggers = [f"cross_chain_relations[{index}].materially_competing=true" for index, relation in enumerate(relations) if relation["materially_competing"]]
    elif any(relation["tension_present"] for relation in relations):
        state, rule = "TENSION", "MC-03"
        triggers = [f"cross_chain_relations[{index}].tension_present=true" for index, relation in enumerate(relations) if relation["tension_present"]]
    elif any(relation["reinforcing"] or relation["coexisting"] for relation in relations):
        state, rule = "COMPATIBLE", "MC-02"
        triggers = [f"cross_chain_relations[{index}].reinforcing/coexisting=true" for index, relation in enumerate(relations) if relation["reinforcing"] or relation["coexisting"]]
    else:
        state, rule = "NONE", "MC-01"
        triggers = ["no reinforcing, coexisting, tension, or materially competing relation"]
    return {
        "state": state,
        "participating_chain_ids": active if state != "NONE" else [],
        "compiler_rule_id": rule,
        "source_field_paths": ["cross_chain_relations", "compiled per-chain applicability"],
        "triggering_structured_facts": triggers,
        "output_state": state,
        "reason": f"Deterministically compiled from structured pairwise relations under {rule}.",
    }
