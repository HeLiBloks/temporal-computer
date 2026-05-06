from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Outcome:
    temporal_hash: str
    result: Any
    stable: bool = False
    provenance: str = "unknown"


class TemporalOutcomeRegister:
    """Content-addressable storage for future outcomes."""

    def __init__(self) -> None:
        self._outcomes: dict[str, Outcome] = {}

    def put(self, outcome: Outcome) -> None:
        if outcome.temporal_hash in self._outcomes:
            raise ValueError(f"outcome already exists for hash {outcome.temporal_hash}")
        self._outcomes[outcome.temporal_hash] = outcome

    def get(self, temporal_hash: str) -> Outcome | None:
        return self._outcomes.get(temporal_hash)

    def has(self, temporal_hash: str) -> bool:
        return temporal_hash in self._outcomes
