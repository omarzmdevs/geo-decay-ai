# Current State

> Snapshot of the project's current status. Updated at the end of every sprint.

## Active Block

Block 1 · Architecture and Infrastructure ([roadmap.md](roadmap.md))

## Active Sprint

Sprint 3 · CI/CD — planned, not started ([log](sprints/sprint-03-cicd.md)). Scope: one
workflow, `.github/workflows/quality-gate.yml`, running the ADR-005 gate on GitHub
Actions through the same `.pre-commit-config.yaml` the commit hook uses, so the gate
keeps one definition (reduced by [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)).
Handoff [009](prompts/009-ci-quality-gate-workflow.md) is written and runs
**interactively only**, because `.github/workflows/**` is protected: the user lifts
the deny entry for that session. Awaiting the user's commit of the sprint plan.

Running in parallel: the feasibility experiment that produces ADR-004
(`docs/experiments/exp-001-*.md`), which is blocked until the user supplies the
bounding box. The bounding box is already a configuration variable (Sprint 2); only
its value is missing.

## Completed Sprints

Sprint 0 · Documentation and Agent Setup ([log](sprints/sprint-00-agent-setup.md))
Sprint 1 · Foundations and Quality Gate — completed 2026-10-14 ([log](sprints/sprint-01-foundations.md))
Sprint 2 · Runtime Foundations — completed 2026-10-21 ([log](sprints/sprint-02-runtime-foundations.md)); handoffs 007 (ACCEPTED 2026-10-16) and 008 (ACCEPTED 2026-10-17) committed.

## Current Milestone

Deliver Sprint 3 (CI/CD), so every push and pull request to `main` is checked by the
quality gate on GitHub, and the feasibility experiment (ADR-004), on top of the
Sprint 2 baseline (validated `Settings`, `BoundingBox` configuration, logging
configured once per process) and the Sprint 1 baseline (skeleton, reference container
with GDAL at system level, enforced quality gate, write-scope guard and pre-commit hook).

## Development Model

Three agent roles — orchestrator, developer (with tester mode) and documenter —
defined in `AGENTS.md` and `.agents/roles/`, with write scopes in
`.agents/policy.yaml`. Agents leave changes in the working tree; the user
stages, reviews and commits.
See [ADR-001](architecture/adr/adr-001-agent-governance.md) and
[ADR-002](architecture/adr/adr-002-operational-roadmap.md).

## Known Issues

- Write-scope guard (`scripts/policy_guard.py`, handoff 003 ACCEPTED,
  2026-10-12) is wired into the commit hook for the secret check (handoff 004
  ACCEPTED, 2026-10-12; `uv run pre-commit install` run by the user on
  2026-10-13). Role scopes are not checked at commit time: the orchestrator
  checks them during verification with `--role`.
- Handoff 003 was run as an experimental, uncommitted tester-mode run; its red
  commit does not exist. See the verification in `docs/prompts/003-policy-guard.md`.
- PDAL is not in the container image and is no longer scheduled for Sprint 9:
  whether it is needed at all is decided by ADR-004, since the raster elevation
  route requires only GDAL (ADR-005 amendment 2026-10-15). Handoffs 002 and 006
  were ACCEPTED 2026-10-14 and committed as d983f96. The image is `debian:trixie`
  with GDAL 3.10.3 at system level.
- External images are pinned by tag, not digest, and apt packages are unpinned,
  so container builds are not bit-reproducible.
- The executed subset of the plan is MVP 1.0, decided in
  [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md), with the per-sprint status
  table in [roadmap.md](roadmap.md). Nothing is deleted from the plan: entries are
  annotated as in, reduced, absorbed, conditional or deferred.

## Last Updated

2026-10-21
