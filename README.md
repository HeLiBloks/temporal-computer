# Temporal Computer

A speculative simulator for a computer with a fourth dimension of resources: time.

The core idea is a **Temporal Outcome Register**:

```text
hash(job + input state + scheduled future time + environment)
  -> known future outcome
```

The scheduler can use a previously registered future outcome immediately, but records temporal debt that must later be repaid by executing the same job and verifying that the resulting hash matches.

This is not real time travel. It is a software model for thinking about:

- content-addressed future results
- temporal debt
- causality validation
- rollback barriers
- deterministic scheduling

## Run

```bash
python -m temporal_computer.demo
```

## Test

```bash
python -m pytest
```

## Concepts

### Temporal hash

A stable hash over:

- job name
- input payload
- target time
- environment version

### Future Outcome Register

Stores outcomes received from a hypothetical future execution.

### Temporal Scheduler

When scheduling a job, it:

1. Computes a temporal hash.
2. Looks up a matching outcome.
3. If found, returns the result immediately and records temporal debt.
4. If not found, runs normally.
5. Later, the debt can be verified by re-running the job and comparing hashes.
