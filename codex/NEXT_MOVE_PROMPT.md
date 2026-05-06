# Codex Prompt: Next Move

Paste this into Codex from the root of the GitHub repo.

```text
You are a senior Python and DevOps engineer working in the repository HeLiBloks/temporal-computer.

Goal:
Turn the current toy temporal-computer simulator into a more serious open-source prototype.

Context:
The project models a speculative Temporal Outcome Register and causality-aware scheduler. It does not implement real time travel. It should be framed as a deterministic scheduling, build-cache, speculative execution, and rollback-safety simulator.

Tasks:
1. Keep the existing public API working.
2. Add a CLI module at temporal_computer/cli.py using only the Python standard library.
3. Add console-script configuration if appropriate, or document `python -m temporal_computer.cli` usage.
4. Add commands:
   - `demo`
   - `hash <job.json>`
   - `schedule <job.json>`
   - `register-put <outcome.json>`
   - `debts-list`
5. Add a simple persistent store under `.temporal/` using JSON files or JSONL.
6. Add tests for the CLI and persistence layer.
7. Add GitHub Actions CI running tests on Python 3.11 and 3.12.
8. Update README with quickstart, CLI examples, architecture summary, and links to docs.
9. Keep implementation clean, typed where useful, and dependency-free unless strongly justified.

Important design constraints:
- Results from the future are speculative unless marked stable.
- Every consumed future result creates temporal debt.
- Debt repayment must verify that the later actual result equals the consumed result.
- A mismatch must raise or record a causality conflict.
- Hashes must be deterministic and include job name, input state, target time, and environment.

Expected outcome:
A working commit with tests passing.

Suggested commit message:
Add CLI and persistent temporal register
```
