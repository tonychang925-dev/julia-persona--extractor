from __future__ import annotations

from typing import Any


def validate_reasoning_frame(frame: dict[str, Any], expected_chain_ids: set[str]) -> None:
    if frame.get("case_id") is None or not isinstance(frame.get("chain_reasoning"), list):
        raise ValueError("reasoning frame requires case_id and chain_reasoning[]")
    row_fields = {
        "chain_id",
        "historical_principle",
        "matched_conditions",
        "limiting_conditions",
        "defeating_conditions",
        "missing_evidence",
        "scope_analysis",
        "authorization_analysis",
        "supersession_analysis",
        "reasoning",
    }
    seen: set[str] = set()
    for row in frame["chain_reasoning"]:
        if not row_fields.issubset(row):
            raise ValueError(f"chain reasoning missing fields: {sorted(row_fields - set(row))}")
        for field in {"matched_conditions", "limiting_conditions", "defeating_conditions"}:
            _validate_conditions(row[field], field)
        for item in row["missing_evidence"]:
            if not {"required_fact", "why_required"}.issubset(item):
                raise ValueError("missing evidence entries require required_fact and why_required")
        _validate_scope(row["scope_analysis"])
        _validate_authorization(row["authorization_analysis"])
        if not {"superseded_prior_judgment_present", "current_governing_revision", "evidence_refs"}.issubset(row["supersession_analysis"]):
            raise ValueError("supersession analysis is incomplete")
        if not str(row["historical_principle"]).strip() or not str(row["reasoning"]).strip():
            raise ValueError("historical principle and reasoning are required")
        if row["chain_id"] in seen:
            raise ValueError(f"duplicate chain reasoning for {row['chain_id']}")
        seen.add(row["chain_id"])
    if seen != expected_chain_ids:
        raise ValueError(f"activated chain coverage mismatch: {sorted(seen ^ expected_chain_ids)}")
    for relation in frame.get("cross_chain_relations", []):
        required = {
            "chain_a",
            "chain_b",
            "relation_evidence",
            "action_implication_a",
            "action_implication_b",
            "reinforcing",
            "coexisting",
            "tension_present",
            "materially_competing",
            "reason",
        }
        if not required.issubset(relation):
            raise ValueError(f"cross-chain relation missing fields: {sorted(required - set(relation))}")
        if relation["chain_a"] == relation["chain_b"]:
            raise ValueError("cross-chain relation cannot relate a chain to itself")


def _validate_conditions(rows: list[dict[str, Any]], name: str) -> None:
    for row in rows:
        if not {"condition", "current_fact_ref", "confidence"}.issubset(row):
            raise ValueError(f"{name} entries require condition, current_fact_ref, and confidence")
        if not str(row["condition"]).strip() or not str(row["current_fact_ref"]).strip():
            raise ValueError(f"{name} condition and current_fact_ref must be non-empty")
        if not 0.0 <= float(row["confidence"]) <= 1.0:
            raise ValueError(f"{name} confidence must be between 0 and 1")


def _validate_scope(value: dict[str, Any]) -> None:
    required = {"subject_match", "counterparty_match", "scope_match", "explicit_inheritance", "inheritance_evidence"}
    if not required.issubset(value):
        raise ValueError(f"scope analysis missing fields: {sorted(required - set(value))}")
    for field in required - {"inheritance_evidence"}:
        if not isinstance(value[field], bool):
            raise ValueError(f"scope.{field} must be boolean")


def _validate_authorization(value: dict[str, Any]) -> None:
    required = {"explicit_authorization_present", "revocable", "scope_limited", "evidence_refs"}
    if not required.issubset(value):
        raise ValueError(f"authorization analysis missing fields: {sorted(required - set(value))}")
    if not isinstance(value["explicit_authorization_present"], bool):
        raise ValueError("explicit_authorization_present must be boolean")
