from __future__ import annotations

from persona_extractor.graph.causal_graph import CausalGraph


def build_graph(experiences: list[dict]) -> CausalGraph:
    graph = CausalGraph()
    graph.nodes = [{"id": item["experience_id"], "type": "causal_experience"} for item in experiences]
    return graph
