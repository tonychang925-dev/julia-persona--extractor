from __future__ import annotations

import re
import json
from typing import Any

from research.v2_5.s1.evaluator import evaluate_native_case
from research.v2_5.state_model import expected_reference


def evaluate_compiled_case(
    *,
    benchmark_case: dict[str, Any],
    reasoning_frame: dict[str, Any],
    compiled: dict[str, Any],
    judgment: dict[str, Any],
    recall: dict[str, Any],
    projected_case: dict[str, Any],
) -> dict[str, Any]:
    native_output = {
        "per_chain_applicability": [
            {
                **row,
                "limiting_conditions": [item["condition"] for item in reasoning_row["limiting_conditions"]],
                "defeating_conditions": [item["condition"] for item in reasoning_row["defeating_conditions"]],
                "missing_evidence": [item["required_fact"] for item in reasoning_row["missing_evidence"]],
            }
            for row, reasoning_row in zip(
                compiled["per_chain_applicability"],
                reasoning_frame["chain_reasoning"],
                strict=True,
            )
        ],
        "composition": compiled["composition"],
        "fresh_judgment": judgment["fresh_judgment"],
        "uncertainty": judgment["uncertainty"],
        "historical_policy_overreach_detected": judgment["historical_policy_overreach_detected"],
        "current_facts": benchmark_case["applicability"]["critical_current_facts"],
    }
    evaluation = evaluate_native_case(
        benchmark_case=benchmark_case,
        native_output=native_output,
        recall=recall,
        projected_case=projected_case,
    )
    evaluation["reasoning_metrics"] = _reasoning_metrics(benchmark_case, reasoning_frame)
    evaluation["layer_error_attribution"] = _layer_attribution(
        benchmark_case=benchmark_case,
        reasoning_frame=reasoning_frame,
        compiled=compiled,
        applicability_match=evaluation["applicability_match"],
        composition_match=evaluation["composition"]["match"],
    )
    evaluation["compiled_state"] = compiled
    evaluation["fresh_judgment"] = judgment
    evaluation["reasoning_frame"] = reasoning_frame
    return evaluation


def aggregate_compiled(cases: list[dict[str, Any]]) -> dict[str, Any]:
    from research.v2_5.s1.evaluator import aggregate_native

    metrics = aggregate_native(cases)
    reasoning_fields = ("RFR", "DCR", "LCR", "SIR", "SUR", "CRC")
    for field in reasoning_fields:
        metrics[field] = _ratio(
            sum(case["reasoning_metrics"][field] for case in cases),
            sum(case["reasoning_metrics"][f"{field}_DENOMINATOR"] for case in cases),
        )
    metrics["layer_error_counts"] = {}
    for case in cases:
        for attribution in case["layer_error_attribution"]:
            key = attribution["layer"]
            metrics["layer_error_counts"][key] = metrics["layer_error_counts"].get(key, 0) + 1
    return metrics


def _reasoning_metrics(case: dict[str, Any], frame: dict[str, Any]) -> dict[str, int]:
    facts = case["applicability"]["critical_current_facts"]
    searchable = _frame_text(frame)
    rfr = sum(bool(_tokens(fact) & _tokens(searchable)) for fact in facts)
    reference = expected_reference(case)
    expected_states = reference["per_chain_applicability"]
    rows = {row["chain_id"]: row for row in frame["chain_reasoning"]}
    dcr_numerator = sum(bool(rows[chain_id]["defeating_conditions"]) for chain_id, state in expected_states.items() if state == "DOES_NOT_APPLY")
    dcr_denominator = sum(state == "DOES_NOT_APPLY" for state in expected_states.values())
    lcr_numerator = sum(bool(rows[chain_id]["limiting_conditions"]) for chain_id, state in expected_states.items() if state == "PARTIALLY_APPLIES")
    lcr_denominator = sum(state == "PARTIALLY_APPLIES" for state in expected_states.values())
    commitment_ids = [
        chain_id
        for chain_id, row in rows.items()
        if any(marker in row["historical_principle"].lower() for marker in ("commitment", "covenant", "confidentiality"))
    ]
    sir_numerator = 0
    for chain_id in commitment_ids:
        expected = expected_states[chain_id]
        scope = rows[chain_id]["scope_analysis"]
        scope_mismatch = not (scope["subject_match"] and scope["counterparty_match"] and scope["scope_match"])
        if expected == "DOES_NOT_APPLY" and scope_mismatch and not scope["explicit_inheritance"]:
            sir_numerator += 1
        elif expected == "INSUFFICIENT_EVIDENCE" and rows[chain_id]["missing_evidence"]:
            sir_numerator += 1
        elif expected == "APPLIES" and scope["explicit_inheritance"]:
            sir_numerator += 1
    superseded_ids = [
        chain_id
        for chain_id, codes in case.get("expected_reason_codes", {}).items()
        if "SUPERSEDED" in codes
    ]
    sur_numerator = sum(bool(rows[chain_id]["supersession_analysis"]["superseded_prior_judgment_present"]) for chain_id in superseded_ids)
    old_conflict = "CONFLICT" in set(case["applicability"]["expected_by_chain"].values())
    relations = frame.get("cross_chain_relations", [])
    crc_numerator = int(old_conflict and any(relation["materially_competing"] for relation in relations))
    return {
        "RFR": rfr,
        "RFR_DENOMINATOR": len(facts),
        "DCR": dcr_numerator,
        "DCR_DENOMINATOR": dcr_denominator,
        "LCR": lcr_numerator,
        "LCR_DENOMINATOR": lcr_denominator,
        "SIR": sir_numerator,
        "SIR_DENOMINATOR": len(commitment_ids),
        "SUR": sur_numerator,
        "SUR_DENOMINATOR": len(superseded_ids),
        "CRC": crc_numerator,
        "CRC_DENOMINATOR": int(old_conflict),
    }


def _layer_attribution(
    *,
    benchmark_case: dict[str, Any],
    reasoning_frame: dict[str, Any],
    compiled: dict[str, Any],
    applicability_match: bool,
    composition_match: bool,
) -> list[dict[str, str]]:
    attributions = []
    reference = expected_reference(benchmark_case)
    rows = {row["chain_id"]: row for row in reasoning_frame["chain_reasoning"]}
    compiled_rows = {row["chain_id"]: row for row in compiled["per_chain_applicability"]}
    for chain_id, expected in reference["per_chain_applicability"].items():
        actual = compiled_rows[chain_id]["state"]
        if expected == actual:
            continue
        provider_signal = False
        if expected == "DOES_NOT_APPLY":
            scope = rows[chain_id]["scope_analysis"]
            provider_signal = bool(rows[chain_id]["defeating_conditions"]) or (
                not (scope["subject_match"] and scope["counterparty_match"] and scope["scope_match"])
                and not scope["explicit_inheritance"]
            )
        elif expected == "INSUFFICIENT_EVIDENCE":
            provider_signal = bool(rows[chain_id]["missing_evidence"])
        elif expected == "PARTIALLY_APPLIES":
            provider_signal = bool(rows[chain_id]["limiting_conditions"])
        layer = "COMPILER_RULE_FAILURE" if provider_signal else "PROVIDER_REASONING_FAILURE"
        attributions.append({"dimension": "per_chain", "chain_id": chain_id, "layer": layer, "expected": expected, "compiled": actual})
    if not composition_match:
        provider_material_relation = any(
            relation["materially_competing"] or relation["tension_present"]
            for relation in reasoning_frame.get("cross_chain_relations", [])
        )
        attributions.append(
            {
                "dimension": "composition",
                "chain_id": None,
                "layer": "COMPILER_RULE_FAILURE" if provider_material_relation else "PROVIDER_REASONING_FAILURE",
                "expected": reference["composition"],
                "compiled": compiled["composition"]["state"],
            }
        )
    return attributions


def _frame_text(frame: dict[str, Any]) -> str:
    return json.dumps(frame, ensure_ascii=False, sort_keys=True)


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 3}


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0
