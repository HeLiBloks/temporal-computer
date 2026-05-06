import json

from temporal_computer.cli import main as cli_main
from temporal_computer.hashing import temporal_hash
from temporal_computer.outcome_register import Outcome, TemporalOutcomeRegister
from temporal_computer.persistence import PersistentTemporalStore
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


def test_persistent_store_keeps_outcomes_and_debts_across_instances(tmp_path):
    store = PersistentTemporalStore(tmp_path / ".temporal")
    outcome = Outcome(
        temporal_hash="abc123",
        result={"status": "ok"},
        stable=False,
        provenance="future packet",
    )

    assert store.put_outcome(outcome) is True

    reloaded = PersistentTemporalStore(tmp_path / ".temporal")
    assert reloaded.get_outcome("abc123") == outcome

    debt = reloaded.record_debt(
        temporal_hash="abc123",
        job={
            "job_name": "compile",
            "input_state": {"code": "int main() { return 0; }"},
            "target_time": "T+5m",
            "environment": {"compiler": "toy"},
        },
        result_used={"status": "ok"},
    )

    debts = PersistentTemporalStore(tmp_path / ".temporal").list_debts()
    assert debts[0]["debt_id"] == debt["debt_id"]
    assert debts[0]["repaid"] is False


def test_cli_hash_register_schedule_and_list_debts(tmp_path, capsys):
    store_path = tmp_path / ".temporal"
    job = {
        "job_name": "compile",
        "input_state": {"code": "int main() { return 0; }"},
        "target_time": "T+5m",
        "environment": {"compiler": "toy-cc-1.0"},
    }
    job_path = tmp_path / "job.json"
    outcome_path = tmp_path / "outcome.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    outcome_path.write_text(
        json.dumps(
            {
                "job": job,
                "result": {"status": "ok", "artifact": "game-build-42"},
                "stable": False,
                "provenance": "future packet",
            }
        ),
        encoding="utf-8",
    )

    assert cli_main(["--store", str(store_path), "hash", str(job_path)]) == 0
    hash_output = json.loads(capsys.readouterr().out)
    assert hash_output["temporal_hash"] == temporal_hash(**job)

    assert cli_main(["--store", str(store_path), "register-put", str(outcome_path)]) == 0
    register_output = json.loads(capsys.readouterr().out)
    assert register_output["status"] == "created"

    assert cli_main(["--store", str(store_path), "schedule", str(job_path)]) == 0
    schedule_output = json.loads(capsys.readouterr().out)
    assert schedule_output["status"] == "future-hit"
    assert schedule_output["result"] == {"status": "ok", "artifact": "game-build-42"}

    assert cli_main(["--store", str(store_path), "debts-list"]) == 0
    debts_output = json.loads(capsys.readouterr().out)
    assert len(debts_output["debts"]) == 1
    assert debts_output["debts"][0]["temporal_hash"] == temporal_hash(**job)


def test_cli_can_repay_debt(tmp_path, capsys):
    store_path = tmp_path / ".temporal"
    job = {
        "job_name": "compile",
        "input_state": {"code": "int main() { return 0; }"},
        "target_time": "T+5m",
        "environment": {"compiler": "toy-cc-1.0"},
    }
    result = {"status": "ok", "artifact": "game-build-42"}
    job_path = tmp_path / "job.json"
    outcome_path = tmp_path / "outcome.json"
    result_path = tmp_path / "result.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    outcome_path.write_text(json.dumps({"job": job, "result": result}), encoding="utf-8")
    result_path.write_text(json.dumps({"result": result}), encoding="utf-8")

    assert cli_main(["--store", str(store_path), "register-put", str(outcome_path)]) == 0
    capsys.readouterr()
    assert cli_main(["--store", str(store_path), "schedule", str(job_path)]) == 0
    debt_id = json.loads(capsys.readouterr().out)["debt_id"]

    assert cli_main(["--store", str(store_path), "debts-repay", debt_id, str(result_path)]) == 0
    repay_output = json.loads(capsys.readouterr().out)
    assert repay_output["status"] == "repaid"
    assert repay_output["debt"]["repaid"] is True
