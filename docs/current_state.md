# Current State

> Snapshot of the project's current status. Updated at the end of every sprint.

## Active Block

Block 1 · Architecture and Infrastructure ([roadmap.md](roadmap.md))

## Active Sprint

Sprint 2 · Runtime Foundations — not yet planned (handoffs pending)

## Completed Sprints

Sprint 0 · Documentation and Agent Setup ([log](sprints/sprint-00-agent-setup.md))
Sprint 1 · Foundations and Quality Gate — completed 2026-10-14 ([log](sprints/sprint-01-foundations.md))

## Current Milestone

Deliver Sprint 2: logging, environment variables and centralised configuration,
on top of the Sprint 1 baseline (skeleton, reference container with GDAL at system
level, enforced quality gate, write-scope guard and pre-commit hook).

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
- PDAL is not in the container image: deferred to Sprint 9 by the ADR-005
  amendment of 2026-10-14 (handoffs 002 and 006, ACCEPTED 2026-10-14, committed
  as d983f96). The image is `debian:trixie` with GDAL 3.10.3 at system level.
- External images are pinned by tag, not digest, and apt packages are unpinned,
  so container builds are not bit-reproducible.
- In sandboxed agent sessions uv cannot use its default cache; workaround
  `UV_CACHE_DIR="$TMPDIR/uv-cache"` (see `.agents/TOOLING.md` → Pending Verification).

## Last Updated

2026-10-14
