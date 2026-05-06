from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .demo import main as demo_main
from .hashing import temporal_hash
from .outcome_register import Outcome
from .persistence import PersistentTemporalStore
from .scheduler import CausalityConflict


class CliError(RuntimeError):
    pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        args.handler(args)
    except (KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except CliError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except CausalityConflict as error:
        print_json({"status": "conflict", "message": str(error)})
        return 2

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="temporal", description="Temporal Computer prototype CLI")
    parser.add_argument("--store", default=".temporal", help="persistent store directory")
    subparsers = parser.add_subparsers(required=True)

    demo = subparsers.add_parser("demo", help="run the built-in demo")
    demo.set_defaults(handler=handle_demo)

    hash_command = subparsers.add_parser("hash", help="compute a deterministic temporal hash")
    hash_command.add_argument("job_json")
    hash_command.set_defaults(handler=handle_hash)

    register_put = subparsers.add_parser("register-put", help="store a known outcome")
    register_put.add_argument("outcome_json")
    register_put.set_defaults(handler=handle_register_put)

    schedule = subparsers.add_parser("schedule", help="consume a known future outcome or record a miss")
    schedule.add_argument("job_json")
    schedule.set_defaults(handler=handle_schedule)

    debts_list = subparsers.add_parser("debts-list", help="list temporal debts")
    debts_list.set_defaults(handler=handle_debts_list)

    debts_repay = subparsers.add_parser("debts-repay", help="repay a debt with an actual result JSON file")
    debts_repay.add_argument("debt_id")
    debts_repay.add_argument("result_json")
    debts_repay.set_defaults(handler=handle_debts_repay)

    return parser


def handle_demo(_args: argparse.Namespace) -> None:
    demo_main()


def handle_hash(args: argparse.Namespace) -> None:
    job = load_job(args.job_json)
    print_json({"temporal_hash": compute_hash(job)})


def handle_register_put(args: argparse.Namespace) -> None:
    payload = load_json(args.outcome_json)
    if not isinstance(payload, dict):
        raise CliError("outcome JSON must be an object")

    temporal_hash_value = payload.get("temporal_hash")
    if temporal_hash_value is None:
        job = payload.get("job")
        if job is None:
            job = payload
        temporal_hash_value = compute_hash(load_job_from_value(job))

    if "result" not in payload:
        raise CliError("outcome JSON must include result")

    outcome = Outcome(
        temporal_hash=temporal_hash_value,
        result=payload["result"],
        stable=bool(payload.get("stable", False)),
        provenance=str(payload.get("provenance", "cli register-put")),
    )

    created = store_from_args(args).put_outcome(outcome)
    print_json(
        {
            "status": "created" if created else "exists",
            "temporal_hash": outcome.temporal_hash,
            "stable": outcome.stable,
            "provenance": outcome.provenance,
        }
    )


def handle_schedule(args: argparse.Namespace) -> None:
    job = load_job(args.job_json)
    store = store_from_args(args)
    temporal_hash_value = compute_hash(job)
    outcome = store.get_outcome(temporal_hash_value)

    if outcome is not None:
        debt = store.record_debt(
            temporal_hash=temporal_hash_value,
            job=job,
            result_used=outcome.result,
        )
        print_json(
            {
                "status": "future-hit",
                "temporal_hash": temporal_hash_value,
                "result": outcome.result,
                "stable": outcome.stable,
                "debt_id": debt["debt_id"],
            }
        )
        return

    if "local_result" in job:
        local_outcome = Outcome(
            temporal_hash=temporal_hash_value,
            result=job["local_result"],
            stable=True,
            provenance="cli local_result",
        )
        store.put_outcome(local_outcome)
        print_json(
            {
                "status": "local-result-stored",
                "temporal_hash": temporal_hash_value,
                "result": local_outcome.result,
                "stable": True,
            }
        )
        return

    print_json(
        {
            "status": "miss",
            "temporal_hash": temporal_hash_value,
            "message": "no future outcome exists and job has no local_result",
        }
    )


def handle_debts_list(args: argparse.Namespace) -> None:
    print_json({"debts": store_from_args(args).list_debts()})


def handle_debts_repay(args: argparse.Namespace) -> None:
    payload = load_json(args.result_json)
    actual_result = payload["result"] if isinstance(payload, dict) and "result" in payload else payload
    debt = store_from_args(args).repay_debt(args.debt_id, actual_result)
    print_json({"status": "repaid", "debt": debt})


def store_from_args(args: argparse.Namespace) -> PersistentTemporalStore:
    return PersistentTemporalStore(args.store)


def load_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise CliError(f"could not read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise CliError(f"invalid JSON in {path}: {error}") from error


def load_job(path: str | Path) -> dict[str, Any]:
    return load_job_from_value(load_json(path))


def load_job_from_value(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CliError("job descriptor must be a JSON object")

    required = ["job_name", "input_state", "target_time"]
    missing = [field for field in required if field not in value]
    if missing:
        raise CliError(f"job descriptor missing required field(s): {', '.join(missing)}")

    return {
        "job_name": str(value["job_name"]),
        "input_state": value["input_state"],
        "target_time": str(value["target_time"]),
        "environment": value.get("environment", {}),
        **({"local_result": value["local_result"]} if "local_result" in value else {}),
    }


def compute_hash(job: dict[str, Any]) -> str:
    environment = job.get("environment", {})
    if not isinstance(environment, dict):
        raise CliError("job environment must be a JSON object")

    return temporal_hash(
        job_name=job["job_name"],
        input_state=job["input_state"],
        target_time=job["target_time"],
        environment=environment,
    )


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
