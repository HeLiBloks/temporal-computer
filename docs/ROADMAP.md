# Roadmap

## Next Move

The best next move is to turn the current toy model into a small but serious developer tool prototype.

Recommended next feature set:

1. Add a CLI.
2. Add GitHub Actions CI.
3. Add structured JSON job descriptors.
4. Add persistent register storage.
5. Add debt repayment and conflict commands.
6. Add docs and diagrams.

## Milestone 0: Repo Hygiene

- Add Apache-2.0 license.
- Add NOTICE.
- Add `CONTRIBUTING.md`.
- Add `CODE_OF_CONDUCT.md`.
- Add GitHub Actions running tests.
- Add `ruff` or basic linting later.

## Milestone 1: CLI

Command sketch:

```bash
temporal hash job.json
temporal register put outcome.json
temporal schedule job.json
temporal debts list
temporal debts repay <debt-id>
temporal demo
```

Example job descriptor:

```json
{
  "job_name": "compile",
  "input_state": {
    "code": "int main() { return 0; }"
  },
  "target_time": "T+5m",
  "environment": {
    "compiler": "toy-cc-1.0",
    "kernel": "temporal-os-0.1"
  }
}
```

## Milestone 2: Persistent Register

Add JSONL or SQLite persistence.

Suggested structure:

```text
.temporal/
  outcomes.jsonl
  debts.jsonl
  events.jsonl
```

Later, use SQLite:

```sql
CREATE TABLE outcomes (
    temporal_hash TEXT PRIMARY KEY,
    result_json TEXT NOT NULL,
    stable INTEGER NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE debts (
    debt_id TEXT PRIMARY KEY,
    temporal_hash TEXT NOT NULL,
    descriptor_json TEXT NOT NULL,
    result_used_json TEXT NOT NULL,
    repaid INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    repaid_at TEXT
);
```

## Milestone 3: Real Build System Analogy

Make the toy scheduler run shell commands in a sandboxed way.

Descriptor:

```json
{
  "job_name": "pytest",
  "command": ["python", "-m", "pytest"],
  "inputs": ["temporal_computer", "tests", "pyproject.toml"],
  "target_time": "T+10m",
  "environment": {
    "python": "3.11"
  }
}
```

Hash should include:

- command
- input file hashes
- environment
- working directory metadata

## Milestone 4: Temporal CI Simulator

Build a CI simulator where future outcomes are equivalent to cached/predicted CI results.

Features:

- record job outcomes
- replay outcomes
- invalidate stale outcomes
- detect nondeterministic jobs
- display debt graph

## Milestone 5: Game Development Scenario

Add examples for game development:

- long-running simulation job
- asset bake job
- compile job
- balance-test job

## Milestone 6: Visualization

Add a small web UI or static report generator:

- outcome graph
- debt graph
- conflict graph
- Mermaid export

## Design Principle

Never present speculative results as stable. Every result should carry a stability state:

```text
stable
speculative
conflicted
invalidated
repaid
```
