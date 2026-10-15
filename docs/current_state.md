# Current State

> Snapshot of the project's current status. Updated at the end of every sprint.

## Active Block

Block 1 · Architecture and Infrastructure ([roadmap.md](roadmap.md))

## Active Sprint

Sprint 2 · Runtime Foundations — not yet planned (handoffs pending). Scope: logging
([ADR-006](architecture/adr/adr-006-logging-strategy.md)), environment variables and
centralised configuration, including the target bounding box as a configuration
variable (four coordinates and the CRS they are expressed in). Running in parallel:
the feasibility experiment that produces ADR-004 (`docs/experiments/exp-001-*.md`),
which is blocked until the user supplies the bounding box.

## Completed Sprints

Sprint 0 · Documentation and Agent Setup ([log](sprints/sprint-00-agent-setup.md))
Sprint 1 · Foundations and Quality Gate — completed 2026-10-14 ([log](sprints/sprint-01-foundations.md))

## Current Milestone

Deliver Sprint 2 and the feasibility experiment, on top of the Sprint 1 baseline
(skeleton, reference container with GDAL at system level, enforced quality gate,
write-scope guard and pre-commit hook).

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
- In sandboxed agent sessions uv cannot use its default cache; workaround
  `UV_CACHE_DIR="$TMPDIR/uv-cache"` (see `.agents/TOOLING.md` → Pending Verification).
- The executed subset of the plan is MVP 1.0, decided in
  [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md), with the per-sprint status
  table in [roadmap.md](roadmap.md). Nothing is deleted from the plan: entries are
  annotated as in, reduced, absorbed, conditional or deferred.

## Last Updated

2026-10-15
