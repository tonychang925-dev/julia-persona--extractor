from __future__ import annotations

from datetime import datetime, timezone
import uuid


def create_manifest() -> dict:
    return {"package_id": f"persona_package_{uuid.uuid4().hex}", "schema_version": "0.1.0", "created_at": datetime.now(timezone.utc).isoformat(), "generator": "julia-persona-extractor/0.1.0"}
