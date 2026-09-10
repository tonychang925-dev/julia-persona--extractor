from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from research.v2_4.structured_applicability_adapter import AnthropicChatAdapter

FRESH_JUDGMENT_SYSTEM_PROMPT = """Historical memory informs the current decision. It does not dictate it.

Use the compiled applicability states, composition state, reasoning evidence, and current facts. Do not resurrect defeated historical policy. Do not infer authority from intimacy or history. Resolve current judgment using present evidence and preserve uncertainty.

Return strict JSON only:
{"case_id":"...","fresh_judgment":"...","uncertainty":"...","historical_policy_overreach_detected":false}
"""


@dataclass
class FreshJudgmentAdapter:
    model: str
    base_url: str
    timeout_seconds: int = 180
    max_tokens: int = 1800
    request_json: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    captures: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {"judgment": []})

    def judge(
        self,
        *,
        case_id: str,
        current_facts: list[str],
        reasoning_frame: dict[str, Any],
        compiled: dict[str, Any],
    ) -> dict[str, Any]:
        user_value = {
            "case_id": case_id,
            "current_facts": current_facts,
            "reasoning_evidence_frame": reasoning_frame,
            "compiled_two_dimensional_state": compiled,
        }
        adapter = AnthropicChatAdapter(
            model=self.model,
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            max_events=1,
            max_tokens=self.max_tokens,
            request_json=self.request_json,
        )
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": 0,
            "thinking": {"type": "disabled"},
            "system": FRESH_JUDGMENT_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": json.dumps(user_value, ensure_ascii=False, sort_keys=True, indent=2)}],
        }
        response = adapter._request(payload)
        text = next((block.get("text") for block in response.get("content", []) if block.get("type") == "text"), None)
        if not text:
            raise RuntimeError("fresh judgment response has no text block")
        parsed = json.loads(text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
        if not {"fresh_judgment", "uncertainty", "historical_policy_overreach_detected"}.issubset(parsed):
            raise ValueError("fresh judgment response is incomplete")
        if not isinstance(parsed["historical_policy_overreach_detected"], bool):
            raise ValueError("historical_policy_overreach_detected must be boolean")
        self.captures["judgment"].append(
            {
                "prompt_sha256": _digest(FRESH_JUDGMENT_SYSTEM_PROMPT + "\n" + json.dumps(user_value, ensure_ascii=False, sort_keys=True)),
                "input_sha256": _digest(user_value),
                "raw_response_sha256": _digest(text),
                "canonical_response_sha256": _digest(parsed),
                "model": self.model,
                "temperature": 0,
                "thinking_mode": "disabled",
                "max_tokens": self.max_tokens,
            }
        )
        return parsed


def build_real_fresh_judgment_adapter(
    *, request_json: Callable[[dict[str, Any]], dict[str, Any]] | None = None
) -> FreshJudgmentAdapter:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is required")
    return FreshJudgmentAdapter(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro"),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic"),
        request_json=request_json,
    )


def _digest(value: object) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
