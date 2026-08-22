from __future__ import annotations

import argparse
import json
from pathlib import Path

from persona_extractor.archive.loader import load_json
from persona_extractor.archive.adapters.chatgpt import normalize_chatgpt_conversation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="persona-extractor")
    subcommands = parser.add_subparsers(dest="command", required=True)
    normalize = subcommands.add_parser("normalize", help="Normalize a conversation archive.")
    normalize.add_argument("input", type=Path)
    normalize.add_argument("--format", choices=["chatgpt"], default="chatgpt")
    normalize.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    raw = load_json(args.input)
    normalized = [normalize_chatgpt_conversation(item, str(args.input)).to_dict() for item in raw] if isinstance(raw, list) else normalize_chatgpt_conversation(raw, str(args.input)).to_dict()
    args.output.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
