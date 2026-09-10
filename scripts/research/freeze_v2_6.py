#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.v2_2.harness import non_temporal_digest
from research.v2_6.runner import file_sha256, provider_identity, schema_digests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cal-result", type=Path, required=True)
    parser.add_argument("--goldset", type=Path, required=True)
    parser.add_argument("--cal-benchmark", type=Path, required=True)
    parser.add_argument("--test-benchmark", type=Path, required=True)
    parser.add_argument("--projected-states", type=Path, required=True)
    parser.add_argument("--v2-4-cal-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError(f"frozen config already exists: {args.output}")
    cal = read_json(args.cal_result)
    copy = dict(cal)
    expected_digest = copy.pop("non_temporal_digest")
    if cal.get("split") != "CAL" or non_temporal_digest(copy) != expected_digest:
        raise RuntimeError("invalid CAL predecessor")
    if any(not result.get("provenance") for result in cal.get("results", [])):
        raise RuntimeError("CAL activation lacks provenance")
    config = {
        "config_id": "V2_6_FROZEN_CONFIG_V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cal_output_sha256": file_sha256(args.cal_result),
        "cal_non_temporal_digest": cal["non_temporal_digest"],
        "provider_identity": cal["execution"]["provider_identity"],
        "schema_and_compiler_digests": schema_digests(),
        "input_hashes": {
            "goldset_sha256": file_sha256(args.goldset),
            "cal_benchmark_sha256": file_sha256(args.cal_benchmark),
            "test_benchmark_sha256": file_sha256(args.test_benchmark),
            "projected_states_sha256": file_sha256(args.projected_states),
            "v2_4_cal_result_sha256": file_sha256(args.v2_4_cal_result),
        },
        "freeze_policy": "NO_TEST_DRIVEN_REASONING_PROMPT_COMPILER_SCHEMA_EVALUATOR_BENCHMARK_OR_THRESHOLD_CHANGE",
    }
    if config["provider_identity"] != provider_identity() or config["schema_and_compiler_digests"] != schema_digests():
        raise RuntimeError("provider, schema, or compiler identity drifted before freeze")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"config": str(args.output), "test_unsealed": True}, sort_keys=True))
    return 0


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError("JSON object required")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
