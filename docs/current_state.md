# Current State

> Snapshot of the project's current status. Updated at the end of every sprint.

## Active Block

Block 1 · Architecture and Infrastructure ([roadmap.md](roadmap.md))

## Active Sprint

Sprint 1 · Foundations and Quality Gate — in progress (handoffs 001, 003, 004 and 005 accepted; 002 pending)

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

- Write-scope guard (`scripts/policy_guard.py`, handoff 003 ACCEPTED,
  2026-10-12) is wired into the commit hook for the secret check (handoff 004
  ACCEPTED, 2026-10-12; `uv run pre-commit install` run by the user on
  2026-10-13). Role scopes are not checked at commit time: the orchestrator
  checks them during verification with `--role`.
- Handoff 003 was run as an experimental, uncommitted tester-mode run; its red
  commit does not exist. See the verification in `docs/prompts/003-policy-guard.md`.

## Last Updated

2026-10-13
