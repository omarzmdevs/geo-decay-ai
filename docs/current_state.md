# Current State

> Snapshot of the project's current status. Updated at the end of every sprint.

## Active Block

Block 2 · MLOps and Data Infrastructure — closed 2026-10-27 ([roadmap.md](roadmap.md)).
Next up: Block 3 · GIS Core, which depends on ADR-004 and therefore on the feasibility
experiment the user has reserved ([next_tasks.md](next_tasks.md)).

## Active Sprint

None. Sprint 4 · MLflow — complete 2026-10-27 ([log](sprints/sprint-04-mlflow.md)). It
delivered a tracking port in the domain, an MLflow adapter and a null adapter in the data
layer, and `geo-decay tracking-smoke`, which records a run with the ADR-008 keys in a local
file store.

Reserved by the user on 2026-10-26, so out of the active slice: the feasibility experiment
that produces ADR-004 (`docs/experiments/exp-001-*.md`), and the bounding box it needs.
ADR-004 still follows from that experiment, and it gates Block 3. The bounding box is
already a configuration variable (Sprint 2); only its value is missing.

## Completed Sprints

Sprint 0 · Documentation and Agent Setup ([log](sprints/sprint-00-agent-setup.md))
Sprint 1 · Foundations and Quality Gate — completed 2026-10-14 ([log](sprints/sprint-01-foundations.md))
Sprint 2 · Runtime Foundations — completed 2026-10-21 ([log](sprints/sprint-02-runtime-foundations.md)); handoffs 007 (ACCEPTED 2026-10-16) and 008 (ACCEPTED 2026-10-17) committed.
Sprint 3 · CI/CD — completed 2026-10-25 ([log](sprints/sprint-03-cicd.md)); handoff 009 ACCEPTED 2026-10-21, closed on the first green GitHub run.
Sprint 4 · MLflow — completed 2026-10-27 ([log](sprints/sprint-04-mlflow.md)); handoffs 010, 011 and 012 ACCEPTED 2026-10-27.

## Current Milestone

Experiment tracking is in place before the first experiment exists (Sprint 4): a tracking
port in the domain, an MLflow adapter confined to the data layer by an import-linter
contract, a null adapter, and composition in delivery, configured through the
`GEO_DECAY_TRACKING_*` variables. Blocks 1 and 2 are closed. The feasibility experiment
(ADR-004) is still open and gates Block 3, on top of the
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
- External images are referenced by tag, not digest, on purpose: the tag keeps floating
  so security patches keep arriving (ADR-005 amendment 2026-10-26). The digest of the
  image that produced a result is recorded per run as `container_image_digest`
  (ADR-008). Apt packages remain unpinned, so container builds are not bit-reproducible.
- The MLflow file store is in maintenance mode. MLflow refuses to open it without
  `MLFLOW_ALLOW_FILE_STORE=true`, which the adapter sets (ADR-008). The migration is
  tracked as MLFLOW-STORE in [next_tasks.md](next_tasks.md).
- The executed subset of the plan is MVP 1.0, decided in
  [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md), with the per-sprint status
  table in [roadmap.md](roadmap.md). Nothing is deleted from the plan: entries are
  annotated as in, reduced, absorbed, conditional or deferred.

## Last Updated

2026-10-27
