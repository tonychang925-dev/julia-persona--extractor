from __future__ import annotations

from typing import Any

COMMITMENT_MARKERS = ("commitment", "covenant", "agreement", "publishing", "approval", "confidentiality")


def compile_applicability(reasoning_frame: dict[str, Any]) -> list[dict[str, Any]]:
    compiled = []
    for row in reasoning_frame["chain_reasoning"]:
        rule, state, inputs = _compile_chain(row)
        compiled.append(
            {
                "chain_id": row["chain_id"],
                "state": state,
                "compiler_rule_id": rule,
                "source_field_paths": [
                    "matched_conditions",
                    "limiting_conditions",
                    "defeating_conditions",
                    "missing_evidence",
                    "scope_analysis",
                    "authorization_analysis",
                    "supersession_analysis",
                ],
                "triggering_structured_facts": inputs,
                "output_state": state,
            }
        )
    return compiled


def _compile_chain(row: dict[str, Any]) -> tuple[str, str, list[str]]:
    scope = row["scope_analysis"]
    scope_mismatch = not all(
        scope[field] for field in ("subject_match", "counterparty_match", "scope_match")
    )
    commitment = any(marker in row["historical_principle"].lower() for marker in COMMITMENT_MARKERS)
    if commitment and scope_mismatch and not scope["explicit_inheritance"]:
        return (
            "PC-SCOPE-01",
            "DOES_NOT_APPLY",
            [
                f"scope_analysis.subject_match={scope['subject_match']}",
                f"scope_analysis.counterparty_match={scope['counterparty_match']}",
                f"scope_analysis.scope_match={scope['scope_match']}",
                f"scope_analysis.explicit_inheritance={scope['explicit_inheritance']}",
            ],
        )
    if row["supersession_analysis"]["superseded_prior_judgment_present"]:
        return (
            "PC-SUPER-01",
            "DOES_NOT_APPLY",
            ["supersession_analysis.superseded_prior_judgment_present=true"],
        )
    missing = row["missing_evidence"]
    identified_structure = row["matched_conditions"] or row["limiting_conditions"] or row["defeating_conditions"]
    if len(missing) >= 2 or not identified_structure:
        return (
            "PC-01",
            "INSUFFICIENT_EVIDENCE",
            [f"missing_evidence[{index}].required_fact={item['required_fact']}" for index, item in enumerate(missing)],
        )
    if row["defeating_conditions"]:
        return (
            "PC-02",
            "DOES_NOT_APPLY",
            [f"defeating_conditions[{index}].condition={item['condition']}" for index, item in enumerate(row["defeating_conditions"])],
        )
    if row["limiting_conditions"] or not all((scope[field],) for field in ("subject_match", "counterparty_match", "scope_match")):
        limits = [f"limiting_conditions[{index}].condition={item['condition']}" for index, item in enumerate(row["limiting_conditions"])]
        for field in ("subject_match", "counterparty_match", "scope_match"):
            if not scope[field]:
                limits.append(f"scope_analysis.{field}=false")
        return "PC-03", "PARTIALLY_APPLIES", limits
    return "PC-04", "APPLIES", [f"matched_conditions[{index}].condition={item['condition']}" for index, item in enumerate(row["matched_conditions"])]
