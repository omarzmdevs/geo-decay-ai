# Current State

> Snapshot of the project's current status. Updated at the end of every sprint.

## Active Block

Block 1 · Architecture and Infrastructure ([roadmap.md](roadmap.md))

## Active Sprint

Sprint 1 · Foundations and Quality Gate — in progress (handoffs 001, 003 and 005 accepted; 002 and 004 pending)

## Completed Sprints

Sprint 0 · Documentation and Agent Setup ([log](sprints/sprint-00-agent-setup.md))

## Current Milestone

Deliver Sprint 1: project skeleton, containerised environment with GDAL/PDAL, and
the automated quality gate (Ruff lint and format, strict MyPy, import-linter, Pytest, pre-commit) together
with the write-scope guard, so that every later sprint starts from an enforced
baseline.

## Development Model

Three agent roles — orchestrator, developer (with tester mode) and documenter —
defined in `AGENTS.md` and `.agents/roles/`, with write scopes in
`.agents/policy.yaml`. Agents leave changes in the working tree; the user
stages, reviews and commits.
See [ADR-001](architecture/adr/adr-001-agent-governance.md) and
[ADR-002](architecture/adr/adr-002-operational-roadmap.md).

## Known Issues

- Write-scope guard exists (`scripts/policy_guard.py`, handoff 003 ACCEPTED,
  2026-10-12), but it is not yet wired into the commit hook: the pre-commit
  hook is handoff 004, pending. Until then, role boundaries depend on review.
- Handoff 003 was run as an experimental, uncommitted tester-mode run; its red
  commit does not exist. See the verification in `docs/prompts/003-policy-guard.md`.

## Last Updated

2026-10-12
