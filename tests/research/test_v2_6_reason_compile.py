
import json
from pathlib import Path

import pytest

from research.v2_6.applicability_compiler import compile_applicability
from research.v2_6.composition_compiler import compile_composition
from research.v2_6.reasoning_adapter import ReasoningEvidenceAdapter
from research.v2_6.schemas import validate_reasoning_frame


def _condition(value):
    return [{"condition": value, "current_fact_ref": "fact", "confidence": 0.9}]


def _missing(value):
    return [{"required_fact": value, "why_required": "Needed to distinguish transfer."}]


def _row(chain_id="GM-CMIR-004", principle="Receiving care reduces over-responsibility.", **overrides):
    row = {
        "chain_id": chain_id,
        "historical_principle": principle,
        "matched_conditions": _condition("current burden"),
        "limiting_conditions": [],
        "defeating_conditions": [],
        "missing_evidence": [],
        "scope_analysis": {
            "subject_match": True,
            "counterparty_match": True,
            "scope_match": True,
            "explicit_inheritance": False,
            "inheritance_evidence": [],
        },
        "authorization_analysis": {
            "explicit_authorization_present": False,
            "revocable": None,
            "scope_limited": None,
            "evidence_refs": [],
        },
        "supersession_analysis": {
            "superseded_prior_judgment_present": False,
            "current_governing_revision": "",
            "evidence_refs": [],
        },
        "reasoning": "The current facts materially match the causal structure.",
    }
    row.update(overrides)
    return row


def _frame(rows=None, relations=None):
    return {
        "case_id": "CASE",
        "chain_reasoning": rows or [_row()],
        "cross_chain_relations": relations or [],
    }


def test_provider_authoritative_state_labels_are_not_required_or_used():
    frame = _frame()
    validate_reasoning_frame(frame, {"GM-CMIR-004"})
    leaked = _frame()
    leaked["state"] = "APPLIES"
    leaked["composition"] = "MATERIAL_CONFLICT"
    leaked["chain_reasoning"][0]["state"] = "PARTIALLY_APPLIES"
    assert compile_applicability(frame) == compile_applicability(leaked)


def test_compiler_rules_cover_all_precedence_paths():
    assert compile_applicability(_frame([_row(missing_evidence=_missing("a") + _missing("b"))]))[0]["compiler_rule_id"] == "PC-01"
    assert compile_applicability(_frame([_row(defeating_conditions=_condition("valid delegation"))]))[0]["compiler_rule_id"] == "PC-02"
    assert compile_applicability(_frame([_row(limiting_conditions=_condition("scope limited"))]))[0]["compiler_rule_id"] == "PC-03"
    assert compile_applicability(_frame([_row()]))[0]["compiler_rule_id"] == "PC-04"


def test_scope_and_supersession_are_first_class_safety_rules():
    scope = {
        "subject_match": True,
        "counterparty_match": False,
        "scope_match": False,
        "explicit_inheritance": False,
        "inheritance_evidence": [],
    }
    commitment = compile_applicability(_frame([_row("GM-CMIR-011", "Historical confidentiality commitment.", scope_analysis=scope)]))[0]
    assert commitment["state"] == "DOES_NOT_APPLY"
    assert commitment["compiler_rule_id"] == "PC-SCOPE-01"
    assert "scope_analysis.explicit_inheritance=False" in commitment["triggering_structured_facts"]
    supersession = {
        "superseded_prior_judgment_present": True,
        "current_governing_revision": "later correction",
        "evidence_refs": ["fact"],
    }
    revised = compile_applicability(_frame([_row(supersession_analysis=supersession)]))[0]
    assert revised["state"] == "DOES_NOT_APPLY"
    assert revised["compiler_rule_id"] == "PC-SUPER-01"


def test_composition_rules_are_deterministic_and_auditable():
    rows = [_row("A"), _row("B")]
    relation = {
        "chain_a": "A",
        "chain_b": "B",
        "relation_evidence": ["evidence"],
        "action_implication_a": "act one",
        "action_implication_b": "act two",
        "reinforcing": False,
        "coexisting": False,
        "tension_present": False,
        "materially_competing": False,
        "reason": "relation",
    }
    assert compile_composition(applicability=compile_applicability(_frame(rows, [])), reasoning_frame=_frame(rows, []))["compiler_rule_id"] == "MC-01"
    relation["coexisting"] = True
    assert compile_composition(applicability=compile_applicability(_frame(rows, [relation])), reasoning_frame=_frame(rows, [relation]))["compiler_rule_id"] == "MC-02"
    relation["coexisting"], relation["tension_present"] = False, True
    assert compile_composition(applicability=compile_applicability(_frame(rows, [relation])), reasoning_frame=_frame(rows, [relation]))["compiler_rule_id"] == "MC-03"
    relation["tension_present"], relation["materially_competing"] = False, True
    composition = compile_composition(applicability=compile_applicability(_frame(rows, [relation])), reasoning_frame=_frame(rows, [relation]))
    assert composition["compiler_rule_id"] == "MC-04"
    assert composition["triggering_structured_facts"]


def test_reasoning_adapter_emits_evidence_before_state_and_judgment():
    provider_frame = _frame()

    def request_json(payload):
        return {"content": [{"type": "text", "text": json.dumps(provider_frame)}]}

    adapter = ReasoningEvidenceAdapter(model="test", base_url="test", request_json=request_json)
    result = adapter.reason(case_id="CASE", current_cue="cue", activated_chains=[{"chain_id": "GM-CMIR-004"}], current_facts=["fact"])
    assert "state" not in result
    assert "composition" not in result
    assert adapter.captures["reasoning"][0]["canonical_response_sha256"]


def test_fresh_judgment_runs_after_compilation_and_reuses_provider_seam():
    from research.v2_6.fresh_judgment_adapter import FreshJudgmentAdapter
    from research.v2_4.structured_applicability_adapter import AnthropicChatAdapter

    def request_json(payload):
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "case_id": "CASE",
                            "fresh_judgment": "Use current facts.",
                            "uncertainty": "Some evidence is missing.",
                            "historical_policy_overreach_detected": False,
                        }
                    ),
                }
            ]
        }

    adapter = FreshJudgmentAdapter(model="test", base_url="test", request_json=request_json)
    compiled = {
        "per_chain_applicability": compile_applicability(_frame()),
        "composition": compile_composition(applicability=compile_applicability(_frame()), reasoning_frame=_frame()),
    }
    judgment = adapter.judge(case_id="CASE", current_facts=["fact"], reasoning_frame=_frame(), compiled=compiled)
    assert judgment["fresh_judgment"]
    assert adapter.captures["judgment"][0]["input_sha256"]
    assert AnthropicChatAdapter.__module__ == "persona_extractor.llm.providers.anthropic_chat_provider"


def test_research_only_reuse_and_no_duplicate_architecture():
    root = Path(__file__).resolve().parents[2]
    forbidden = {
        "new_provider",
        "semantic_engine",
        "causal_extractor_v2",
        "new_validator",
        "memory_activation_engine",
        "runtime_policy_engine",
    }
    for file in (root / "research/v2_6").glob("*.py"):
        text = file.read_text(encoding="utf-8")
        assert not any(name in text for name in forbidden)
    assert (root / "research/v2_2/persona_extractor_adapter.py").exists()
    assert (root / "research/v2_4/structured_applicability_adapter.py").exists()
