#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.v2_6.applicability_compiler import compile_applicability
from research.v2_6.composition_compiler import compile_composition
from research.v2_6.fresh_judgment_adapter import build_real_fresh_judgment_adapter
from research.v2_6.reasoning_adapter import build_real_reasoning_adapter
from research.v2_6.runner import file_sha256, provider_identity, run_split, schema_digests, utc_now, write_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goldset", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--projected", type=Path, required=True)
    parser.add_argument("--v2-4-cal-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError(f"CAL result already exists: {args.output}")
    execution = _execution(args)
    run = run_split(
        goldset_path=args.goldset,
        benchmark_path=args.benchmark,
        split="CAL",
        reasoning_adapter=build_real_reasoning_adapter(),
        judgment_adapter=build_real_fresh_judgment_adapter(),
        projected_path=args.projected,
        v2_4_cal_result_path=args.v2_4_cal_result,
        execution=execution,
    )
    _validate_cal(run)
    run["execution"]["completed_at"] = utc_now()
    write_run(run, args.output)
    print(json.dumps({"split": "CAL", "cases": len(run["results"]), "metrics": run["metrics"], "output": str(args.output)}, sort_keys=True))
    return 0


def _execution(args: argparse.Namespace) -> dict:
    return {
        "schema_version": "2.6.0",
        "gate": "V2_6_REASON_FIRST_COMPILE_SECOND",
        "run_mode": "REASONING_COMPILER_THEN_FRESH_JUDGMENT_CAL",
        "started_at": utc_now(),
        "repository_head": git_head(),
        "repository_state": "RESEARCH_ONLY",
        "input_hashes": {
            "goldset_sha256": file_sha256(args.goldset),
            "benchmark_sha256": file_sha256(args.benchmark),
            "projected_states_sha256": file_sha256(args.projected),
            "v2_4_cal_result_sha256": file_sha256(args.v2_4_cal_result),
        },
        "provider_identity": provider_identity(),
        "schema_digests": schema_digests(),
        "authority_boundary": {
            "proposal_only": True,
            "semantic_activation_authority": False,
            "compiler_research_only": True,
            "current_judgment_authority": False,
            "c05_admission": False,
            "runtime_activation": False,
        },
    }


def _validate_cal(run: dict) -> None:
    for result in run["results"]:
        frame = result["reasoning_frame"]
        if not frame["chain_reasoning"] or any(not row["scope_analysis"] for row in frame["chain_reasoning"]):
            raise RuntimeError("CAL reasoning frame or scope analysis is incomplete")
        first = compile_applicability(frame)
        second = compile_applicability(frame)
        if first != second:
            raise RuntimeError("CAL compiler is not deterministic")
        if compile_composition(applicability=first, reasoning_frame=frame) != compile_composition(applicability=second, reasoning_frame=frame):
            raise RuntimeError("CAL composition compiler is not deterministic")
        if not result["fresh_judgment"]["fresh_judgment"].strip():
            raise RuntimeError("CAL fresh judgment is empty")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
