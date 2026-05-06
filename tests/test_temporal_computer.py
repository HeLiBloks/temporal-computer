from temporal_computer.hashing import temporal_hash
from temporal_computer.outcome_register import Outcome, TemporalOutcomeRegister
from temporal_computer.scheduler import TemporalScheduler, CausalityConflict


def test_temporal_hash_is_stable():
    a = temporal_hash(
        job_name="compile",
        input_state={"b": 2, "a": 1},
        target_time="T+5m",
        environment={"compiler": "toy"},
    )
    b = temporal_hash(
        job_name="compile",
        input_state={"a": 1, "b": 2},
        target_time="T+5m",
        environment={"compiler": "toy"},
    )
    assert a == b


def test_scheduler_uses_future_outcome_and_records_debt():
    env = {"compiler": "toy"}
    register = TemporalOutcomeRegister()
    h = temporal_hash(
        job_name="add",
        input_state={"x": 1, "y": 2},
        target_time="T+1m",
        environment=env,
    )
    register.put(Outcome(h, 3, provenance="future packet"))

    scheduler = TemporalScheduler(register, env)
    result = scheduler.schedule(
        job_name="add",
        input_state={"x": 1, "y": 2},
        target_time="T+1m",
        func=lambda s: s["x"] + s["y"],
    )

    assert result == 3
    assert len(scheduler.debts) == 1


def test_debt_conflict_detected():
    env = {"compiler": "toy"}
    register = TemporalOutcomeRegister()
    h = temporal_hash(
        job_name="add",
        input_state={"x": 1, "y": 2},
        target_time="T+1m",
        environment=env,
    )
    register.put(Outcome(h, 999, provenance="future packet"))

    scheduler = TemporalScheduler(register, env)
    scheduler.schedule(
        job_name="add",
        input_state={"x": 1, "y": 2},
        target_time="T+1m",
        func=lambda s: s["x"] + s["y"],
    )

    try:
        scheduler.repay_debt(scheduler.debts[0], lambda s: s["x"] + s["y"])
    except CausalityConflict:
        pass
    else:
        raise AssertionError("expected causality conflict")
