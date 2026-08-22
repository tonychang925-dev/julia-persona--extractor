from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CausalGraph:
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"nodes": self.nodes, "edges": self.edges}
