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
and image quality) ACCEPTED 2026-11-06, from a live run the user committed with its outputs,
step 3 (section 7 · the spectral check) ACCEPTED 2026-11-06 — no near infrared is served —
and step 4 (sections 8 to 8.3 · the cadastral footprints) ACCEPTED 2026-11-08, from four
live runs: the cadastre serves 787 buildings over the extent, only in tiles under an area
ceiling it enforces, and its condition attribute is uniform, so it is **not** a weak label
source and the manual labelling pass stands. All five feature sources it publishes have
now been asked, and the storey count lives on the building parts, not on the buildings.
**Step 5 (section 9 · elevation availability) ACCEPTED 2026-11-11**, from a live run by the user
that measured elevation through two WCS 2.0.1 services: four raster products cover the whole
extent (terrain and surface ≈5 m, building and vegetation height ≈2.5 m; first LiDAR coverage,
one epoch, whole metres, resampled cells). `mdsn_e025` is building height and `mdsn_v025`
vegetation height, read from the footprint overlay of section 9.1 (cells above zero inside vs
outside footprints: 82.4 % vs 6.4 % for building height, 8.3 % vs 28.5 % for vegetation). The
point cloud was not pursued, by the user's decision, and a raster-only route exists, so PDAL is
not needed for anything measured. Step 6 (sections 10 and 11 · example buildings and the
labelling table) was split in three on 2026-11-14: **6a (section 10 · multi-epoch chip
strips) ACCEPTED 2026-11-14**, from a live run by the user: 12 example buildings by area
tertile and quadrant, one strip each with the year on every chip, and `out/strips.csv` with
one row per building and year asked (108); 86 of 108 chips kept. 2012 and 2015 cover only the east edge, and the
epochs are not co-registered to the footprint to the same degree. **6b (section 11 · the
labelling table) ACCEPTED 2026-11-14**: `out/candidates.csv` with 787 cadastral rows, 0 manual,
12 with strip and label year (2023), and empty label columns for the manual pass. 6c (sections
10.2 and 10.3 · manual samples on their own map) ACCEPTED 2026-11-15: 7 manual samples, 3 inside
the extent and 4 outside, strips for 6 of 7, and the table at 794 rows with 2 rows' manual work
carried. Step 6 ACCEPTED 2026-11-15. **Step 7 (section 12 · findings) ACCEPTED 2026-11-16**:
the findings are generated from the run and the measured part written to `out/summary.md`, with
15 findings and 10 problems, none unmeasured; questions 1 answered, 2 and 3 partly answered, and
4 not answered, because the manual labelling pass is outside this block by the user's decision of
2026-11-15. **Step 8 (close) is next** — the duplicate cadastral replies fixed in `eda.py` and the
folder's README — then the orchestrator's EXP-001 Analysis and Conclusion, and ADR-004. The
sprint produces no production code:
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
capabilities, the per-epoch figures and the cadastral reference are settled — about
7 usable epochs of the 21 advertised at a measured 0.25 m/px, and 787 buildings with a
median footprint of 70.9 m² whose attributes cannot label them — while the elevation figures are
measured (step 5), the example chip strips, the manual samples and the labelling table exist (step 6),
and the findings are written (step 7). The labelling figures stay unmeasured: the manual pass is
outside this block.

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
015, with steps 0 to 7 accepted. The
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
  route requires only GDAL (ADR-005 amendment 2026-10-15), and so does the route measured in
  step 5 of handoff 015. Handoffs 002 and 006
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

2026-11-16
