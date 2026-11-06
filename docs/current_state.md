# Current State

> Snapshot of the project's current status. Updated at the end of every sprint.

## Active Block

Block 3 · GIS Core, entered through its gate: Sprint 5 · Feasibility Instrumentation is
active ([log](sprints/sprint-05-feasibility-instrumentation.md)). Block 2 · MLOps and Data
Infrastructure closed 2026-10-27 ([roadmap.md](roadmap.md)). Block 3 depends on ADR-004,
which follows from the feasibility experiment ([next_tasks.md](next_tasks.md)).

## Active Sprint

Sprint 5 · Feasibility Instrumentation — active, started 2026-11-04. Handoff 013 (EDA helper
module and provider configuration) ACCEPTED 2026-11-04. Handoff 014 (exploratory notebook)
ACCEPTED 2026-11-04, but **its deliverable was discarded by the user** the same day, after the
first live run showed the extent selector did not work; it is superseded by handoff 015, which
rebuilds the notebook one section at a time, in Spanish, each section confirmed against the
live services before the next is written. **Handoff 015 is in progress**: step 0 (the
self-contained folder in `notebooks/exp-001/`) ACCEPTED 2026-11-04, step 1 (section 4 ·
provider capabilities) ACCEPTED 2026-11-05 and step 2 (sections 5 and 6 · epoch availability
and image quality) ACCEPTED 2026-11-06, from a live run the user committed with its outputs;
**step 3 (section 7 · the spectral check) is next**. The sprint produces no production code:
it makes EXP-001 measurable and re-measurable by the user's own run. The extent is no longer
open: it was drawn and committed on 2026-11-04 as `notebooks/exp-001/out/extent.json`
(`EPSG:25830`, 1.204224 km², 21 × 14 tiles).

Sprint 4 · MLflow — complete 2026-10-27 ([log](sprints/sprint-04-mlflow.md)). It
delivered a tracking port in the domain, an MLflow adapter and a null adapter in the data
layer, and `geo-decay tracking-smoke`, which records a run with the ADR-008 keys in a local
file store.

The feasibility experiment that produces ADR-004 (`docs/experiments/exp-001-*.md`) is in
progress through this sprint. ADR-004 still follows from its measured figures, and it gates
Block 3. The bounding box is a configuration variable (Sprint 2) and its value is now chosen
and committed, so the experiment advances one notebook section per session. The provider
capabilities and the per-epoch figures are settled — about 7 usable epochs of the 21
advertised, at a measured 0.25 m/px — while the cadastral, elevation and labelling figures
are still unmeasured.

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
`GEO_DECAY_TRACKING_*` variables. Blocks 1 and 2 are closed. Sprint 5 has accepted handoffs
013 (the EDA helper module and provider configuration) and 014 (the notebook, whose deliverable
the user then discarded), and is now rebuilding the notebook section by section under handoff
015, with steps 0, 1 and 2 accepted. The
feasibility experiment (ADR-004) is still open and gates Block 3, on top of the
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
- A plain `uv sync` cannot prune the `eda` group inside the agent sandbox: it must delete
  a `tornado` test `*.key` file, which the sandbox denies. Tracked as SANDBOX-SYNC in
  [next_tasks.md](next_tasks.md); see handoff 013 Verification, note 7.
- The sandbox proxy answers a blocked host with HTTP 403, not a connection failure, so a
  refused request is recorded as `unknown`, never `absent`. See handoff 013 Verification,
  note 1.
- The executed subset of the plan is MVP 1.0, decided in
  [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md), with the per-sprint status
  table in [roadmap.md](roadmap.md). Nothing is deleted from the plan: entries are
  annotated as in, reduced, absorbed, conditional or deferred.

## Last Updated

2026-11-06
