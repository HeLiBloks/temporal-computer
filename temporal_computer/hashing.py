from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize data deterministically for stable hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def temporal_hash(
    *,
    job_name: str,
    input_state: Any,
    target_time: str,
    environment: dict[str, Any],
) -> str:
    """Create a content-addressed identity for a future computation."""
    payload = {
        "job_name": job_name,
        "input_state": input_state,
        "target_time": target_time,
        "environment": environment,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
