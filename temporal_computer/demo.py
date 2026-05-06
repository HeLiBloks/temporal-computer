from __future__ import annotations

from .hashing import temporal_hash
from .outcome_register import Outcome, TemporalOutcomeRegister
from .scheduler import TemporalScheduler


def compile_game_code(source: dict[str, str]) -> dict[str, str]:
    if "syntax_error" in source["code"]:
        return {"status": "failed", "log": "syntax error"}
    return {"status": "ok", "artifact": "game-build-42"}


def main() -> None:
    env = {"kernel": "temporal-os-0.1", "compiler": "toy-cc-1.0"}
    register = TemporalOutcomeRegister()

    job = {
        "job_name": "compile",
        "input_state": {"code": "int main() { return 0; }"},
        "target_time": "T+5m",
        "environment": env,
    }

    h = temporal_hash(**job)

    # Pretend this result arrived from the future.
    register.put(
        Outcome(
            temporal_hash=h,
            result={"status": "ok", "artifact": "game-build-42"},
            stable=False,
            provenance="future packet",
        )
    )

    scheduler = TemporalScheduler(register, env)

    result = scheduler.schedule(
        job_name=job["job_name"],
        input_state=job["input_state"],
        target_time=job["target_time"],
        func=compile_game_code,
    )

    print("Result returned immediately:")
    print(result)
    print()
    print("Temporal debts:")
    for debt in scheduler.debts:
        print(f"- {debt.temporal_hash[:12]}... target={debt.target_time} repaid={debt.repaid}")

    print()
    print("Repaying first debt by executing the job later...")
    scheduler.repay_debt(scheduler.debts[0], compile_game_code)
    print(f"Debt repaid: {scheduler.debts[0].repaid}")


if __name__ == "__main__":
    main()
