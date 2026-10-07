# Next Tasks

> The active slice of the plan. The full block and sprint structure lives in
> [roadmap.md](roadmap.md), which is the operational source of truth.
> Updated at the end of every sprint.

## Active Sprint

- [ ] **Sprint 1 · Foundations and Quality Gate** (Block 1) — folder structure,
  Python environment, `pyproject.toml`, Docker, Docker Compose, DevContainer with
  GDAL/PDAL; Ruff, Black, strict MyPy, Pytest, pre-commit; `tests/unit/` and
  `tests/acceptance/`; `scripts/policy_guard.py` with its tests and hook.
  See [sprint-01-foundations.md](sprints/sprint-01-foundations.md).

## Blocked On

These decisions must be recorded before Sprint 1 starts, because the sprint
creates `pyproject.toml` and the folder structure and the orchestrator owns
system-level architecture:

- [ ] **ADR-003** — `src/` layout and layer boundaries.
- [ ] **ADR-005** — dependency and environment manager.

## Next Up

- [ ] **Sprint 2 · Runtime Foundations** (Block 1) — logging, environment
  variables, centralised configuration.
- [ ] **Sprint 3 · CI/CD** (Block 1) — GitHub Actions: lint, format, type check,
  tests, Docker build.
- [ ] **Block 2 · MLOps and Data Infrastructure** — Sprints 4–6: MLflow, DVC,
  reproducibility.

## Governance and Architecture Debt

Tracked findings from the project review, deferred with their identifiers:

- [ ] **E6 / E5 · ADR-003 and ADR-004** — `src/` layout and layer boundaries;
  CRS, tiling and data contracts. ADR-003 blocks Sprint 1.
- [ ] **E5 · ADR-005** — dependency manager. Blocks Sprint 1.
- [ ] **E1 · Write-scope enforcement** — `scripts/policy_guard.py` validating the
  working-tree diff against `.agents/policy.yaml`, plus its pre-commit hook. Until it
  exists, role scopes rely on review alone. Scheduled in Sprint 1.
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

2026-10-07
