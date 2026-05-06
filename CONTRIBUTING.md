# Contributing

Contributions are welcome.

## Project Framing

Temporal Computer is a speculative simulator and systems-design playground. Avoid presenting it as real time-travel technology.

Useful contribution areas:

- deterministic hashing
- scheduling models
- build-system analogies
- reproducible execution
- conflict detection
- rollback semantics
- documentation and diagrams

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

## Commit Style

Use clear commit messages:

```text
Add temporal debt persistence
Document scheduler state machine
Fix deterministic hashing for nested payloads
```

## Design Rules

- Speculative outcomes must be labeled.
- Hash inputs must be deterministic.
- Causality conflicts must fail visibly.
- Prefer small, testable abstractions.
- Keep the toy model understandable.
