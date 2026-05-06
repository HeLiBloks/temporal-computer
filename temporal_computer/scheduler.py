from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .hashing import temporal_hash
from .outcome_register import TemporalOutcomeRegister, Outcome


@dataclass
class TemporalDebt:
    temporal_hash: str
    job_name: str
    input_state: Any
    target_time: str
    environment: dict[str, Any]
    result_used: Any
    repaid: bool = False


class CausalityConflict(RuntimeError):
    pass


class TemporalScheduler:
    """A toy scheduler that can consume registered future outcomes."""

    def __init__(self, register: TemporalOutcomeRegister, environment: dict[str, Any]) -> None:
        self.register = register
        self.environment = environment
        self.debts: list[TemporalDebt] = []

    def schedule(
        self,
        *,
        job_name: str,
        input_state: Any,
        target_time: str,
        func: Callable[[Any], Any],
    ) -> Any:
        h = temporal_hash(
            job_name=job_name,
            input_state=input_state,
            target_time=target_time,
            environment=self.environment,
        )

        future_outcome = self.register.get(h)
        if future_outcome is not None:
            self.debts.append(
                TemporalDebt(
                    temporal_hash=h,
                    job_name=job_name,
                    input_state=input_state,
                    target_time=target_time,
                    environment=self.environment,
                    result_used=future_outcome.result,
                )
            )
            return future_outcome.result

        result = func(input_state)
        self.register.put(
            Outcome(
                temporal_hash=h,
                result=result,
                stable=True,
                provenance="local execution",
            )
        )
        return result

    def repay_debt(self, debt: TemporalDebt, func: Callable[[Any], Any]) -> None:
        actual_result = func(debt.input_state)

        if actual_result != debt.result_used:
            raise CausalityConflict(
                f"future outcome mismatch for {debt.temporal_hash}: "
                f"used {debt.result_used!r}, produced {actual_result!r}"
            )

        debt.repaid = True
