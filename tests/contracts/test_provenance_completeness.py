from __future__ import annotations


def test_persona_element_has_lineage_to_archive():
    package = {
        "manifest": {"package_id": "pkg_001"},
        "experiences": [
            {"experience_id": "exp_001", "provenance_refs": ["archive_001:message_001"]}
        ],
        "causal_graph": {
            "nodes": [
                {
                    "node_id": "node_001",
                    "node_type": "causal_experience",
                    "derived_from": ["exp_001"],
                    "provenance_refs": ["archive_001:message_001"],
                }
            ],
            "edges": [],
        },
        "provenance": {
            "archive_refs": ["archive_001"],
            "experience_refs": ["exp_001"],
            "lineage_complete": True,
        },
    }

    archive_refs = set(package["provenance"]["archive_refs"])
    experience_refs = {item["experience_id"] for item in package["experiences"]}

    for element in package["causal_graph"]["nodes"]:
        assert element["provenance_refs"]
        assert set(element["derived_from"]).issubset(experience_refs)
        assert any(ref.split(":", 1)[0] in archive_refs for ref in element["provenance_refs"])
