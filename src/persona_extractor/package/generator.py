from __future__ import annotations

from persona_extractor.package.manifest import create_manifest


def generate_persona_package(experiences: list[dict], causal_graph: dict | None = None) -> dict:
    return {"manifest": create_manifest(), "identity": {}, "experiences": experiences, "causal_graph": causal_graph or {"nodes": [], "edges": []}, "relationship": {}, "behavior": {}, "provenance": {"coverage": "prototype"}, "validation": {"status": "review_prepared"}, "evolution": {"lifecycle_status": "creation"}}
