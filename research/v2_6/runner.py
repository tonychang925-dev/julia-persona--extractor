from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from research.v2_2.harness import non_temporal_digest
from research.v2_2.persona_extractor_adapter import V2_2PersonaExtractorAdapter, load_goldset
from research.v2_3.benchmark_source import PRINCIPLES
from research.v2_6.applicability_compiler import compile_applicability
from research.v2_6.composition_compiler import compile_composition
from research.v2_6.evaluator import aggregate_compiled, evaluate_compiled_case


def load_benchmark(path: str | Path, split: str) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        document = json.load(handle)
    cases = document.get("cases", [])
    if not cases or any(case.get("split") != split for case in cases):
        raise RuntimeError(f"benchmark isolation failure for {split}: {path}")
    return deepcopy(cases)


def run_split(
    *,
    goldset_path: str | Path,
    benchmark_path: str | Path,
    split: str,
    reasoning_adapter: Any,
    judgment_adapter: Any,
    projected_path: str | Path,
    v2_4_cal_result_path: str | Path | None = None,
    execution: dict[str, Any],
) -> dict[str, Any]:
    goldset = load_goldset(goldset_path)
    cases = load_benchmark(benchmark_path, split)
    persona_adapter = V2_2PersonaExtractorAdapter(goldset)
    with Path(projected_path).open(encoding="utf-8") as handle:
        projected_by_case = {case["case_id"]: case for case in json.load(handle)["cases"]}
    if split == "CAL" and v2_4_cal_result_path is not None:
        with Path(v2_4_cal_result_path).open(encoding="utf-8") as handle:
            v2_4_cal = json.load(handle)
        from research.v2_5.projector import project_v2_4_result

        projected_by_case.update(
            {
                case["case_id"]: case
                for case in project_v2_4_result(test_result=v2_4_cal, audit_result=_cal_audit_projection(v2_4_cal))
            }
        )
    evaluated = []
    for case in cases:
        proposals = persona_adapter.propose(cue=case["cue"], anchor_plan=case["anchor_plan"])
        validations = [persona_adapter.validate(proposal, eligibility=case["eligibility"]) for proposal in proposals]
        activated_ids = [
            proposal["causal_chain"]["chain_id"]
            for proposal, validation in zip(proposals, validations, strict=True)
            if validation["v2_2_eligibility"]["state"] == "ACTIVATED_FOR_AUTOBIOGRAPHICAL_RECALL_CONSIDERATION"
        ]
        activated_chains = []
        for proposal in proposals:
            chain_id = proposal["causal_chain"]["chain_id"]
            if chain_id not in activated_ids:
                continue
            claim = _claim(goldset, chain_id, proposal["causal_chain"]["claim_id"])
            activated_chains.append(
                {
                    "chain_id": chain_id,
                    "historical_principle": PRINCIPLES[chain_id],
                    "audited_claims": [claim["claim_supported"]],
                    "historical_condition_structure": _principle_entry(case, chain_id),
                    "scope_subject_counterparty_metadata": _principle_entry(case, chain_id),
                    "supersession_or_correction_metadata": {
                        "revision_state": case.get("expected_revision_state", {}).get(chain_id, "ACTIVE_OR_UNREVISED")
                    },
                    "provenance": {
                        "claim_id": claim["claim_id"],
                        "source_evidence_ref": claim["m0_binding"]["source_evidence_ref"],
                        "bundle_ref": claim["m0_binding"].get("bundle_ref"),
                    },
                }
            )
        reasoning_frame = reasoning_adapter.reason(
            case_id=case["case_id"],
            current_cue=case["cue"]["text"],
            activated_chains=activated_chains,
            current_facts=case["applicability"]["critical_current_facts"],
        )
        applicability = compile_applicability(reasoning_frame)
        composition = compile_composition(applicability=applicability, reasoning_frame=reasoning_frame)
        compiled = {
            "case_id": case["case_id"],
            "per_chain_applicability": applicability,
            "composition": composition,
        }
        judgment = judgment_adapter.judge(
            case_id=case["case_id"],
            current_facts=case["applicability"]["critical_current_facts"],
            reasoning_frame=reasoning_frame,
            compiled=compiled,
        )
        reasoning_frame["provider_captures"] = deepcopy(reasoning_adapter.captures)
        judgment["provider_captures"] = deepcopy(judgment_adapter.captures)
        recall = {
            "proposed_chain_ids": [proposal["causal_chain"]["chain_id"] for proposal in proposals],
            "activated_chain_ids": activated_ids,
            "proposals": proposals,
            "validation_results": validations,
        }
        evaluated.append(
            evaluate_compiled_case(
                benchmark_case=case,
                reasoning_frame=reasoning_frame,
                compiled=compiled,
                judgment=judgment,
                recall=recall,
                projected_case=projected_by_case[case["case_id"]],
            )
        )
    run = {
        "schema_version": "2.6.0",
        "experiment": "V2_6_REASON_FIRST_COMPILE_SECOND",
        "split": split,
        "sealed": split == "TEST",
        "predecessor_gate": {
            "name": "V2_5_S1_NATIVE_2D_APPLICABILITY_COMPOSITION",
            "status": "FAIL_INFORMATIVE",
            "result_non_temporal_digest": "3f70885f4330fd03d0bb2310314ac6c9fab1c90a45ad9c3dfc87eef968660990",
        },
        "results": evaluated,
        "metrics": aggregate_compiled(evaluated),
        "execution": execution,
    }
    run["non_temporal_digest"] = non_temporal_digest(run)
    return run


def provider_identity() -> dict[str, Any]:
    from research.v2_6.fresh_judgment_adapter import FRESH_JUDGMENT_SYSTEM_PROMPT
    from research.v2_6.reasoning_adapter import REASONING_SYSTEM_PROMPT

    return {
        "provider_type": "anthropic",
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "adapter": "AnthropicChatAdapter/ReasoningEvidenceAdapter/FreshJudgmentAdapter",
        "temperature": 0,
        "thinking_mode": "disabled",
        "reasoning_max_tokens": 4200,
        "judgment_max_tokens": 1800,
        "structured_output_mode": "strict_json_text_without_authoritative_state_fields",
        "reasoning_prompt_digest": hashlib.sha256(REASONING_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "judgment_prompt_digest": hashlib.sha256(FRESH_JUDGMENT_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "api_key_exposed": False,
    }


def schema_digests() -> dict[str, str]:
    root = Path(__file__).parent
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.glob("*.py"))}


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def write_run(run: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _claim(goldset: dict[str, Any], chain_id: str, claim_id: str) -> dict[str, Any]:
    for claim in goldset["chains"][chain_id]["claims"]:
        if claim["claim_id"] == claim_id:
            return claim
    raise RuntimeError(f"claim not found: {claim_id}")


def _principle_entry(case: dict[str, Any], chain_id: str) -> dict[str, Any]:
    for principle in case.get("expected_principles", []):
        if principle["chain_id"] == chain_id:
            return principle
    return {}


def _cal_audit_projection(cal_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "cases": [
            {
                "case_id": result["case_id"],
                "state_match": result["expected_frame_decisions"] == result["actual_frame_decisions"],
                "category": "CAL_COMPILER_COMPATIBILITY",
                "expected_states": result["expected_frame_decisions"],
            }
            for result in cal_result["results"]
        ]
    }
