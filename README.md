# Temporal Computer

A speculative Python simulator for a computer where **time is treated as a schedulable resource**.

The project explores a fictional-but-useful architecture built around:

- temporal hashes
- a Temporal Outcome Register
- future outcome lookup
- causality debt
- conflict detection
- rollback-oriented thinking

It does **not** implement real time travel. It is a systems-design playground for ideas related to deterministic build systems, speculative execution, CI acceleration, reproducible computation, and future-result validation.

## Core Idea

```text
hash(job + input state + scheduled future time + environment)
  -> known future outcome
```

If a future outcome is already known, the scheduler may return it immediately, but it records a **temporal debt**. That debt must later be repaid by executing the same job and verifying that the result matches.

```mermaid
flowchart TD
    Job[Job Descriptor] --> Hash[Temporal Hash]
    Hash --> TOR[Temporal Outcome Register]
    TOR -->|Hit| Outcome[Return Future Outcome Now]
    TOR -->|Miss| Execute[Execute Locally]
    Outcome --> Debt[Record Temporal Debt]
    Execute --> Store[Store Stable Outcome]
    Debt --> Verify[Verify Later]
    Verify -->|Match| Repaid[Debt Repaid]
    Verify -->|Mismatch| Conflict[Causality Conflict]
```

## Quickstart

```bash
python -m temporal_computer.demo
```

## Tests

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## Repository Structure

```text
temporal_computer/
  hashing.py            deterministic temporal hash
  outcome_register.py   content-addressed future outcomes
  scheduler.py          scheduler + debt validation
  demo.py               minimal working example

docs/
  ARCHITECTURE.md       detailed architecture
  CONCEPTS.md           design concepts from the discussion
  MERMAID.md            diagram collection
  ROADMAP.md            next technical steps

codex/
  NEXT_MOVE_PROMPT.md   prompt for Codex to continue the repo
  FOLLOWUP_PROMPTS.md   future Codex tasks
```

## Why This Is Interesting

The fictional time-machine framing maps surprisingly well onto real engineering problems:

| Time-computer concept | Real-world analogy |
|---|---|
| Future outcome | cached or predicted result |
| Temporal hash | content-addressed build key |
| Temporal debt | deferred verification obligation |
| Paradox | cache invalidation or nondeterminism |
| Rollback barrier | transaction boundary |
| Temporal scheduler | predictive CI/build scheduler |

## Documentation

Start here:

- [Architecture](docs/ARCHITECTURE.md)
- [Concepts](docs/CONCEPTS.md)
- [Mermaid diagrams](docs/MERMAID.md)
- [Roadmap](docs/ROADMAP.md)
- [Codex next move](codex/NEXT_MOVE_PROMPT.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
