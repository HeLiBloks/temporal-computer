# Follow-up Codex Prompts

## Add SQLite persistence

```text
Replace the JSON/JSONL persistence layer with SQLite while preserving the public interfaces. Add migrations or table initialization. Add tests proving outcomes and debts persist across process restarts.
```

## Add shell-job execution

```text
Add support for job descriptors that execute shell commands safely using subprocess. Hash command, environment, working directory, and selected input file hashes. Capture stdout, stderr, exit code, and duration. Add tests using harmless commands only.
```

## Add Mermaid report generation

```text
Add a command `temporal report --format markdown` that emits a Markdown report with Mermaid diagrams of outcomes, debts, and conflicts. Include tests that verify the generated report contains valid Mermaid fenced blocks.
```

## Add game-development examples

```text
Add examples under examples/game-dev showing compile, asset bake, simulation, and balance-test jobs. Each example should include a job descriptor, expected outcome, and README explaining the scenario.
```

## Add conflict policy engine

```text
Add a policy engine for conflicts with modes: reject, recompute, rollback-required, and branch. Do not implement real branching yet; model it as metadata and state transitions. Add tests for each policy.
```
