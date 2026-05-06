from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashing import canonical_json
from .outcome_register import Outcome
from .scheduler import CausalityConflict


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class PersistentTemporalStore:
    """JSONL-backed storage for outcomes, debts, and audit events."""

    def __init__(self, root: str | Path = ".temporal") -> None:
        self.root = Path(root)
        self.outcomes_path = self.root / "outcomes.jsonl"
        self.debts_path = self.root / "debts.jsonl"
        self.events_path = self.root / "events.jsonl"

    def put_outcome(self, outcome: Outcome) -> bool:
        existing = self.get_outcome(outcome.temporal_hash)
        record = {
            **asdict(outcome),
            "created_at": utc_now(),
        }

        if existing is not None:
            if asdict(existing) != asdict(outcome):
                raise ValueError(f"conflicting outcome already exists for {outcome.temporal_hash}")
            return False

        self._append_jsonl(self.outcomes_path, record)
        self.record_event("outcome.put", {"temporal_hash": outcome.temporal_hash})
        return True

    def get_outcome(self, temporal_hash: str) -> Outcome | None:
        for record in self._read_jsonl(self.outcomes_path):
            if record["temporal_hash"] == temporal_hash:
                return Outcome(
                    temporal_hash=record["temporal_hash"],
                    result=record["result"],
                    stable=record.get("stable", False),
                    provenance=record.get("provenance", "unknown"),
                )
        return None

    def record_debt(
        self,
        *,
        temporal_hash: str,
        job: dict[str, Any],
        result_used: Any,
    ) -> dict[str, Any]:
        debt = {
            "debt_id": uuid.uuid4().hex,
            "temporal_hash": temporal_hash,
            "job": job,
            "result_used": result_used,
            "repaid": False,
            "created_at": utc_now(),
            "repaid_at": None,
            "conflict": None,
        }
        self._append_jsonl(self.debts_path, debt)
        self.record_event("debt.recorded", {"debt_id": debt["debt_id"], "temporal_hash": temporal_hash})
        return debt

    def list_debts(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self.debts_path)

    def repay_debt(self, debt_id: str, actual_result: Any) -> dict[str, Any]:
        debts = self.list_debts()
        for debt in debts:
            if debt["debt_id"] != debt_id:
                continue

            if debt["result_used"] != actual_result:
                debt["conflict"] = {
                    "expected": debt["result_used"],
                    "actual": actual_result,
                    "detected_at": utc_now(),
                }
                self._write_jsonl(self.debts_path, debts)
                self.record_event("debt.conflict", {"debt_id": debt_id})
                raise CausalityConflict(f"future outcome mismatch for debt {debt_id}")

            debt["repaid"] = True
            debt["repaid_at"] = utc_now()
            self._write_jsonl(self.debts_path, debts)
            self.record_event("debt.repaid", {"debt_id": debt_id})
            return debt

        raise KeyError(f"unknown debt id {debt_id}")

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._append_jsonl(
            self.events_path,
            {
                "event_type": event_type,
                "payload": payload,
                "created_at": utc_now(),
            },
        )

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _write_jsonl(self, path: Path, records: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(f"{canonical_json(record)}\n" for record in records),
            encoding="utf-8",
        )

    def _append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{canonical_json(record)}\n")
