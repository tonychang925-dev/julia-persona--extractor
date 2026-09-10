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

from research.v2_6.fresh_judgment_adapter import build_real_fresh_judgment_adapter
from research.v2_6.reasoning_adapter import build_real_reasoning_adapter
from research.v2_6.runner import file_sha256, provider_identity, run_split, schema_digests, utc_now, write_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goldset", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--projected", type=Path, required=True)
    parser.add_argument("--frozen-config", type=Path, required=True)
    parser.add_argument("--cal-result", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir / "V2_6_TEST_RESULT_V1.json"
    frames_output = args.output_dir / "V2_6_REASONING_FRAMES_TEST_V1.json"
    compiled_output = args.output_dir / "V2_6_COMPILED_STATES_TEST_V1.json"
    if any(path.exists() for path in (output, frames_output, compiled_output)):
        raise RuntimeError("one-shot TEST artifacts already exist")
    config = read_json(args.frozen_config)
    _verify_frozen(config, args)
    execution = {
        "schema_version": "2.6.0",
        "gate": "V2_6_REASON_FIRST_COMPILE_SECOND",
        "run_mode": "REASONING_COMPILER_THEN_FRESH_JUDGMENT_SEALED_TEST",
        "started_at": utc_now(),
        "repository_head": git_head(),
        "repository_state": "RESEARCH_ONLY",
        "input_hashes": {
            "goldset_sha256": file_sha256(args.goldset),
            "benchmark_sha256": file_sha256(args.benchmark),
            "projected_states_sha256": file_sha256(args.projected),
        },
        "provider_identity": provider_identity(),
        "schema_and_compiler_digests": schema_digests(),
        "frozen_config": {
            "config_id": config["config_id"],
            "config_sha256": file_sha256(args.frozen_config),
            "cal_non_temporal_digest": config["cal_non_temporal_digest"],
        },
        "authority_boundary": {
            "proposal_only": True,
            "semantic_activation_authority": False,
            "compiler_research_only": True,
            "current_judgment_authority": False,
            "c05_admission": False,
            "runtime_activation": False,
        },
    }
    run = run_split(
        goldset_path=args.goldset,
        benchmark_path=args.benchmark,
        split="TEST",
        reasoning_adapter=build_real_reasoning_adapter(),
        judgment_adapter=build_real_fresh_judgment_adapter(),
        projected_path=args.projected,
        execution=execution,
    )
    run["execution"]["completed_at"] = utc_now()
    write_run(run, output)
    write_run(
        {
            "artifact_id": "V2_6_REASONING_FRAMES_TEST_V1",
            "cases": [result["reasoning_frame"] for result in run["results"]],
        },
        frames_output,
    )
    write_run(
        {
            "artifact_id": "V2_6_COMPILED_STATES_TEST_V1",
            "cases": [result["compiled_state"] for result in run["results"]],
        },
        compiled_output,
    )
    print(json.dumps({"split": "TEST", "cases": len(run["results"]), "metrics": run["metrics"], "output": str(output)}, sort_keys=True))
    return 0


def _verify_frozen(config: dict, args: argparse.Namespace) -> None:
    if config.get("config_id") != "V2_6_FROZEN_CONFIG_V1":
        raise RuntimeError("invalid frozen config")
    if file_sha256(args.cal_result) != config["cal_output_sha256"]:
        raise RuntimeError("CAL result differs from frozen config")
    if file_sha256(args.goldset) != config["input_hashes"]["goldset_sha256"]:
        raise RuntimeError("goldset changed after freeze")
    if file_sha256(args.benchmark) != config["input_hashes"]["test_benchmark_sha256"]:
        raise RuntimeError("TEST benchmark changed after freeze")
    if file_sha256(args.projected) != config["input_hashes"]["projected_states_sha256"]:
        raise RuntimeError("projected states changed after freeze")
    if provider_identity() != config["provider_identity"]:
        raise RuntimeError("provider identity changed after freeze")
    if schema_digests() != config["schema_and_compiler_digests"]:
        raise RuntimeError("reasoning schema or compiler changed after freeze")


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError("JSON object required")
    return value


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
