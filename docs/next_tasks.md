# Next Tasks

> The active slice of the plan. The full block and sprint structure lives in
> [roadmap.md](roadmap.md), which is the operational source of truth.
> Updated at the end of every sprint.

## Active Sprint

- [ ] **Sprint 1 · Foundations and Quality Gate** (Block 1) — folder structure,
  Python environment, `pyproject.toml`, Docker, Docker Compose, DevContainer with
  GDAL/PDAL; Ruff (lint and format), strict MyPy, import-linter, Pytest,
  pre-commit; `tests/unit/` and `tests/acceptance/`; `scripts/policy_guard.py`
  with its tests and hook.
  See [sprint-01-foundations.md](sprints/sprint-01-foundations.md).

## Blocked On

Sprint 1 handoffs 001–004 are written (`docs/prompts/`). The ADR-005
protected-path changes were applied and uv installed on 2026-10-08. Only the
per-session lift for the interactive handoffs remains open.

- [x] `AGENTS.md`, `.agents/roles/developer.md` — Black replaced by Ruff format;
  import-linter added to the gate.
- [x] `.agents/TOOLING.md` — developer launch allowlist uses `Bash(uv run *)`.
- [x] `.agents/policy.yaml` — developer scope gains `uv.lock`, `.python-version`,
  `tests/acceptance/.gitkeep`.
- [x] `.claude/settings.json` — sandbox network allowlist for PyPI and Python
  downloads.
- [ ] Infrastructure deny entries lifted for the interactive session of
  handoffs 002 and 004 (per session, not in the shared settings).
- [x] uv installed on the host.

## Next Up

- [ ] **Sprint 2 · Runtime Foundations** (Block 1) — logging, environment
  variables, centralised configuration.
- [ ] **Sprint 3 · CI/CD** (Block 1) — GitHub Actions: lint, format, type check,
  tests, Docker build.
- [ ] **Block 2 · MLOps and Data Infrastructure** — Sprints 4–6: MLflow, DVC,
  reproducibility.

## Governance and Architecture Debt

Tracked findings from the project review, deferred with their identifiers:

- [x] **E6 · ADR-003** — `src/` layout and layer boundaries (2026-10-08).
- [ ] **E5 · ADR-004** — CRS, tiling and data contracts. Required before Block 3.
- [x] **E5 · ADR-005** — dependency manager (2026-10-08).
- [ ] **E1 · Write-scope enforcement** — `scripts/policy_guard.py` validating the
  working-tree diff against `.agents/policy.yaml`, plus its pre-commit hook. Until it
  exists, role scopes rely on review alone. Scheduled in Sprint 1.
  Guard done (handoff 003, ACCEPTED 2026-10-12); pre-commit hook pending (handoff 004).
- [ ] **W2 · Secret pattern drift** — the guard must validate the full `.env.*`
  glob; the tool deny list enumerates variants one by one and can fall behind.
- [ ] **W3 · Permission coverage** — verify empirically whether `Edit(...)` deny
  rules also cover file writes, and record the result in `.agents/TOOLING.md`.
- [ ] **W12 · Redundant rule** — the `--no-verify` deny entry is covered by the
  broader commit deny; remove it.

## Backlog

- [ ] Research state-of-the-art for abandoned infrastructure detection (Sprint 11).
- [ ] Evaluate PNOA/LiDAR data sources and download APIs (Sprint 8).
- [ ] Define abandonment indicators taxonomy (Sprint 14).

## Last Updated

2026-10-12
