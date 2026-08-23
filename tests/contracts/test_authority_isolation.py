from __future__ import annotations

EXTRACTOR_FORBIDDEN_FIELDS = {
    "runtime_eligibility",
    "activation_weight",
    "governance_status",
    "runtime_scope",
}


def test_extractor_package_does_not_emit_core_authority_fields():
    extractor_package = {
        "manifest": {"package_id": "pkg_001"},
        "experiences": [],
        "causal_graph": {"nodes": [], "edges": []},
        "provenance": {"archive_refs": [], "experience_refs": [], "lineage_complete": True},
        "validation": {"extractor_status": "review_pending", "review_status": "pending"},
        "lifecycle": {"current_state": "review_pending", "history": []},
    }

    assert EXTRACTOR_FORBIDDEN_FIELDS.isdisjoint(extractor_package.keys())
