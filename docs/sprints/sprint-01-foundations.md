# Sprint 01 · Foundations and Quality Gate

## Block

Block 1 · Architecture and Infrastructure

## Goal

Create the professional project structure and the automated quality gate that
every later sprint depends on. No business logic.

## Execution Mode

**Interactive, with explicit user approval.** Most deliverables are protected
paths (`Dockerfile*`, `docker-compose*.yml`, `.devcontainer/`,
`.pre-commit-config.yaml`), which `.agents/policy.yaml` forbids changing in a
headless run.

## Requirements

* Standard project structure: `src/`, `tests/unit/`, `tests/acceptance/`, `scripts/`.
* Python 3.12 environment and dependencies managed by uv, declared in
  `pyproject.toml` and locked in `uv.lock`.
* Docker, Docker Compose and DevContainer with GDAL and PDAL installed at system
  level.
* Quality gate: Ruff (lint and format), strict MyPy, import-linter, Pytest,
  pre-commit with local hooks run through `uv run`.
* Write-scope guard enforcing `.agents/policy.yaml` on the working-tree diff.

## Prerequisites

* [ADR-003](../architecture/adr/adr-003-src-layout-and-layer-boundaries.md) —
  `src/` layout and layer boundaries. Recorded 2026-10-08.
* [ADR-005](../architecture/adr/adr-005-dependency-and-environment-manager.md) —
  uv, Python 3.12, gate tooling. Recorded 2026-10-08.
* The protected-path follow-ups listed in ADR-005, applied by the user.

## Tasks

Execution order: 001 → 005 → 002 → 003 (tester mode, user commit, implementation) → 004.
005 runs before any other developer task, so that no developer can rewrite Markdown with `ruff format .`.

- [x] [001](../prompts/001-project-skeleton-and-gate.md) — base `pyproject.toml`
      (hatchling, four packages, `dev` group, Ruff/MyPy/import-linter/Pytest
      configuration), `uv.lock`, `.python-version` and the ADR-003 directory
      structure. Headless.
- [x] [005](../prompts/005-ruff-python-only.md) — restrict Ruff to Python
      files; Ruff 0.16 also formats Markdown, protected paths included. Headless.
- [ ] [002](../prompts/002-container-and-devcontainer.md) — `Dockerfile`,
      `docker-compose.yml` and DevContainer with GDAL and PDAL at system level.
      Interactive.
- [x] [003](../prompts/003-policy-guard.md) — `scripts/policy_guard.py` with
      acceptance and unit tests. Headless (tester mode, then implementation).
- [x] [004](../prompts/004-pre-commit-gate.md) — `.pre-commit-config.yaml`
      with the full gate and the secret check. Interactive.
- [x] User: add `scripts/policy_guard.py` to the tool deny list once 003 is
      accepted, so no agent can modify its own guard.
- [ ] Orchestrator: verify the agent environment inside the container. That
      means checking that the most restrictive headless permission mode behaves
      as documented, and that the sandbox works with Docker and with package
      installation (see `.agents/TOOLING.md` → Pending Verification).

## Deliverable

A project that runs with no business logic, whose quality gate runs
automatically, and whose write scopes are enforced rather than merely documented.

## Handoffs Executed

- [001 · Project skeleton and quality gate](../prompts/001-project-skeleton-and-gate.md) — ACCEPTED — 2026-10-08
- [005 · Restrict Ruff to Python files](../prompts/005-ruff-python-only.md) — ACCEPTED — 2026-10-11
- [003 · Write-scope policy guard](../prompts/003-policy-guard.md) — ACCEPTED (experimental run; criteria 1, 2 and 5 not verifiable as written) — 2026-10-12
- [004 · Pre-commit quality gate](../prompts/004-pre-commit-gate.md) — ACCEPTED — 2026-10-12

## Notes

- Black is not part of the stack (ADR-005): Ruff format is the only formatter;
  strict MyPy stays in the gate.
- The skeleton and the tool configuration are merged into one handoff (001),
  because `mypy`, `lint-imports` and `pytest` cannot pass without the packages.
- The commit hook runs the policy guard with `--secrets-only`. A commit
  legitimately combines several roles and authorised protected changes, so role
  scopes are checked by the orchestrator at verification time
  (`--role <role>`), not at commit time.
- Handoff 003 uses `Acceptance tests: yes` although the guard is not domain
  logic: it is the only automatic enforcement of write scopes.

## Documents Updated

- [docs/current_state.md](../current_state.md)
- [docs/next_tasks.md](../next_tasks.md)

## Date Started

2026-10-08

## Date Completed

<!-- YYYY-MM-DD -->
