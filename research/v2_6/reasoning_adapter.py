from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from research.v2_4.structured_applicability_adapter import AnthropicChatAdapter
from research.v2_6.schemas import validate_reasoning_frame

REASONING_SYSTEM_PROMPT = """You are producing research-only evidence and condition reasoning for activated autobiographical causal chains.

Do not choose or output an authoritative applicability category. Do not choose or output an authoritative composition category. A deterministic compiler will discretize states later.

For every activated chain independently:
- identify current facts that match the historical causal structure;
- identify current facts that materially limit transfer;
- identify current facts that defeat transfer;
- identify information required but currently missing;
- explicitly analyze subject identity, counterparty identity, scope, and commitment inheritance;
- explicitly detect authorization or delegation;
- explicitly detect superseded historical judgments and later corrected cognition;
- do not assume inheritance or authorization merely because history, intimacy, or commitment exists.

For each pair of relevant chains, analyze their current-action implications and whether they reinforce, coexist, create tension, or materially compete. Do not collapse chains into one blended principle.

Preserve uncertainty where current evidence is incomplete. Do not produce the final judgment yet.

Return strict JSON only:
{"case_id":"...","chain_reasoning":[{"chain_id":"...","historical_principle":"...","matched_conditions":[{"condition":"...","current_fact_ref":"...","confidence":0.0}],"limiting_conditions":[{"condition":"...","current_fact_ref":"...","confidence":0.0}],"defeating_conditions":[{"condition":"...","current_fact_ref":"...","confidence":0.0}],"missing_evidence":[{"required_fact":"...","why_required":"..."}],"scope_analysis":{"subject_match":true,"counterparty_match":true,"scope_match":true,"explicit_inheritance":false,"inheritance_evidence":[]},"authorization_analysis":{"explicit_authorization_present":false,"revocable":null,"scope_limited":null,"evidence_refs":[]},"supersession_analysis":{"superseded_prior_judgment_present":false,"current_governing_revision":"","evidence_refs":[]},"reasoning":"..."}],"cross_chain_relations":[{"chain_a":"...","chain_b":"...","relation_evidence":["..."],"action_implication_a":"...","action_implication_b":"...","reinforcing":false,"coexisting":false,"tension_present":false,"materially_competing":false,"reason":"..."}]}
"""


@dataclass
class ReasoningEvidenceAdapter:
    model: str
    base_url: str
    timeout_seconds: int = 180
    max_tokens: int = 4200
    request_json: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    captures: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {"reasoning": []})

    def reason(
        self,
        *,
        case_id: str,
        current_cue: str,
        activated_chains: list[dict[str, Any]],
        current_facts: list[str],
    ) -> dict[str, Any]:
        user_value = {
            "case_id": case_id,
            "current_cue": current_cue,
            "current_explicit_facts": current_facts,
            "activated_historical_causal_chains": activated_chains,
        }
        raw = self._request(REASONING_SYSTEM_PROMPT, user_value)
        raw = _normalize_empty_lists(raw)
        validate_reasoning_frame(raw, {chain["chain_id"] for chain in activated_chains})
        return raw

    def _request(self, system_prompt: str, user_value: dict[str, Any]) -> dict[str, Any]:
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
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": json.dumps(user_value, ensure_ascii=False, sort_keys=True, indent=2)}
            ],
        }
        response = adapter._request(payload)
        text = next((block.get("text") for block in response.get("content", []) if block.get("type") == "text"), None)
        if not text:
            raise RuntimeError("reasoning provider response has no text block")
        parsed = json.loads(_strip_json_fence(text))
        if not isinstance(parsed, dict):
            raise ValueError("reasoning provider response must be an object")
        self.captures["reasoning"].append(
            {
                "prompt_sha256": _digest(system_prompt + "\n" + json.dumps(user_value, ensure_ascii=False, sort_keys=True)),
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


def build_real_reasoning_adapter(
    *, request_json: Callable[[dict[str, Any]], dict[str, Any]] | None = None
) -> ReasoningEvidenceAdapter:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is required")
    return ReasoningEvidenceAdapter(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro"),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic"),
        request_json=request_json,
    )


def _digest(value: Any) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _strip_json_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        value = value.removeprefix("```json").removeprefix("```").removesuffix("```")
    return value.strip()


def _normalize_empty_lists(frame: dict[str, Any]) -> dict[str, Any]:
    for row in frame.get("chain_reasoning", []):
        for field in ("matched_conditions", "limiting_conditions", "defeating_conditions", "missing_evidence"):
            value = row.get(field)
            if value in ("", [], None, "[]"):
                row[field] = []
            elif isinstance(value, list):
                row[field] = [item for item in value if isinstance(item, dict) and str(item.get("condition") or item.get("required_fact", "")).strip()]
    if frame.get("cross_chain_relations") in ("", [], None, "[]"):
        frame["cross_chain_relations"] = []
    return frame
