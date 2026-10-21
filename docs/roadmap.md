# Roadmap

> **Operational source of truth for the plan.** Every agent reads this file to
> know which block and sprint exist and what each one delivers. The active slice
> is in [next_tasks.md](next_tasks.md) and the live status in
> [current_state.md](current_state.md).
>
> `docs/tfm/TFM_v1.md` holds the original thesis narrative in Spanish. It is
> reference material, not the execution plan: where the two differ, this file
> governs and the deviation is recorded in an ADR
> ([ADR-002](architecture/adr/adr-002-operational-roadmap.md)).

## Sprint Conditions

Every sprint must:

1. Add new functionality.
2. Keep the project fully working.
3. Not break the existing architecture.

## Phases

| Phase | Scope | Sprints |
|---|---|---|
| **MVP (v1.0)** | Blocks 1–7 — a complete, defensible system | 1–23 |
| **Extended (v2.0)** | Block 8 — agentic orchestration and RAG | 24–26 |
| **Optimisation** | Final block — performance, accuracy, scalability | — |

---

## MVP 1.0 — Active Scope

The plan below is kept in full. **MVP 1.0** is the subset executed now, decided
in [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md). Everything else stays
on record, reduced or deferred to a later iteration; nothing is planned or
launched from a deferred entry.

**Objective.** Given a bounding box — supplied as a configuration variable, not
hard-coded — download and prepare the data, tile it, detect built structures
and compute an explainable abandonment index for each detection, with the
comparative experiment recorded and reproducible. Detection and the index are
the core; the rest feeds them or shows their results.

**Two rules that shape it.** Nothing is built before the sprint that first
needs it. Indicators are a pluggable collection: an input that is unavailable
removes one indicator group and is recorded as absent, never blocking the
pipeline.

**Before Sprint 8**, ADR-004 is produced from a feasibility experiment
(`docs/experiments/exp-001-*.md`) measuring what the data actually supports for
one bounding box. It fixes the CRS, tiling, the inter-stage data contracts, the
elevation route and the detection strategy. Tracked in
[next_tasks.md](next_tasks.md).

| Sprint | Status in MVP 1.0 |
|---|---|
| 1 · Foundations and Quality Gate | done, reused unchanged |
| 2 · Runtime Foundations | **in** — also adds the bounding-box variable |
| 3 · CI/CD | **in**, reduced to one workflow running the gate |
| 4 · MLflow | **in**, reduced to a local file store |
| 5 · DVC | deferred — replaced by the acquisition manifest with checksums in Sprint 8 |
| 6 · Reproducibility | absorbed — seeds and externalised configuration in Sprint 2; the environment is already fixed by the lockfile and the container |
| 7 · Spatial Database | deferred — results are files until a query workload exists |
| 8 · Data Download | **in** — adds the acquisition manifest |
| 9 · GIS Processing | **in** — PDAL conditional, decided by ADR-004 |
| 10 · Tiling System | **in** |
| 11 · Comparative Research | reduced — the detection strategy is chosen in ADR-004 from measured evidence rather than from a full benchmark |
| 12 · Detector Implementation | **in** |
| 13 · Individual Extraction | **in** |
| 14 · Indicator Definition | **in** |
| 15 · Automatic Extraction | **in** |
| 16 · Assessment Engine | **in** |
| 17 · Zero-shot System | absorbed — Sprints 12 and 16 already are the untrained pipeline (pretrained detector, GIS analysis, heuristic rules); Sprint 19 compares against it rather than rebuilding it |
| 18 · Fine-Tuning | conditional — only if the feasibility experiment shows enough labelled examples can be produced |
| 19 · Scientific Comparison | **in** — indicator ablation at minimum |
| 20 · API | **in**, reduced to a small documented endpoint set |
| 21 · Frontend | reduced — one MapLibre page: draw the bounding box, launch the run, see the results; no React project |
| 22 · Results | absorbed into Sprint 21 |
| 23 · Reports | deferred |
| 24–26 · Agents and RAG | deferred |
| Final · Optimisation | deferred, including areas larger than one bounding box |

---

# Block 1 · Architecture and Infrastructure

Build the project's technical base. No AI or data functionality yet.

> Deviation from TFM_v1, recorded in [ADR-002](architecture/adr/adr-002-operational-roadmap.md):
> the quality gate and the policy guard move into Sprint 1, so everything
> structural is settled before any business logic is written. The original
> Sprint 2 keeps its slot with the runtime concerns that are not structural.

## Sprint 1 · Foundations and Quality Gate

**Objective.** Create the professional project structure and the automated
quality gate that every later sprint depends on.

**Deliverable.** A project that runs with no business logic, whose every commit
is validated automatically and whose write scopes are enforced.

Scope: folder structure (ADR-003), Python environment with uv (ADR-005),
`pyproject.toml`, Docker, Docker Compose, DevContainer with GDAL at system
level (PDAL deferred to Sprint 9, ADR-005 amendment); Ruff (lint and format), strict MyPy, import-linter, Pytest, pre-commit; `tests/unit/` and `tests/acceptance/`;
`scripts/policy_guard.py` with its tests and its hook.

## Sprint 2 · Runtime Foundations

**Objective.** Prepare the project for maintainable execution.

**Deliverable.** Centralised configuration and logging in place, with no secret
read from anywhere but the environment.

Scope: logging ([ADR-006](architecture/adr/adr-006-logging-strategy.md)),
environment variables, centralised configuration — including the target
bounding box, held as a configuration variable (four coordinates and the CRS
they are expressed in) so the covered extent is selected without touching code.
Later entry points fill the same variable: the CLI, the API and the map
selection of Sprint 21.

## Sprint 3 · CI/CD

**Objective.** Automate the development process.

**Deliverable.** A working CI pipeline.

Scope: GitHub Actions running lint, formatting, type checking and tests.
*Reduced in MVP 1.0 to one workflow running the quality gate
([ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md), amendment 2026-10-21):
the Docker build stays out of CI while the DevContainer builds the image
daily, and CD has nothing to deploy before Sprints 20 and 21.*

---

# Block 2 · MLOps and Data Infrastructure

Establish experiment tracking, data versioning and reproducibility *before*
working with data or models, so that from the first downloaded file and the
first evaluated model everything is recorded, versioned and reproducible.

## Sprint 4 · MLflow

**Objective.** Configure experiment tracking.

**Deliverable.** MLflow integrated and ready to record any later experiment,
logging experiments, models, metrics and hyperparameters.

## Sprint 5 · DVC

**Objective.** Configure versioning of data and artefacts.

**Deliverable.** DVC configured and ready to version the data downloaded in later
blocks: datasets, weights, models and results.

## Sprint 6 · Reproducibility

**Objective.** Guarantee that any experiment can be repeated.

**Deliverable.** Reproducibility verified end to end, with deterministic seeds,
externalised configuration, reproducible DVC pipelines and documented
environments.

---

# Block 3 · GIS Core

Build the system's geospatial infrastructure.

## Sprint 7 · Spatial Database

**Objective.** Integrate PostgreSQL and PostGIS.

**Deliverable.** A fully working spatial database.

## Sprint 8 · Data Download

**Objective.** Obtain the required data automatically.

**Deliverable.** Automatic download working with versioning integrated.

## Sprint 9 · GIS Processing

**Objective.** Prepare the data for the AI stage.

**Deliverable.** Processed data plus scripts for visual inspection.

Includes PDAL at system level in the container image, built from a pinned
source release (ADR-005 amendment 2026-10-14). Whether PDAL is needed at all is
decided by ADR-004: the raster elevation route requires only GDAL
(ADR-005 amendment 2026-10-15).

## Sprint 10 · Tiling System

**Objective.** Split the study area automatically.

**Deliverable.** A complete tile generation system.

---

# Block 4 · Infrastructure Detection

Detect infrastructure automatically.

## Sprint 11 · Comparative Research

**Objective.** Compare detection methodologies in an experimental phase before
building the definitive system.

**Deliverable.** A documented comparison that selects the methodology.

## Sprint 12 · Detector Implementation

**Objective.** Build the definitive detection system.

**Deliverable.** A working detector that can export results for validation in
QGIS or Jupyter.

## Sprint 13 · Individual Extraction

**Objective.** Turn every detection into an independent entity.

**Deliverable.** Each detection stored as an independent geospatial entity.

---

# Block 5 · Abandonment Assessment

Turn detections into an explainable abandonment score.

## Sprint 14 · Indicator Definition

**Objective.** Define which variables describe abandonment.

**Deliverable.** A documented taxonomy of abandonment indicators.

## Sprint 15 · Automatic Extraction

**Objective.** Implement automatic computation of the defined indicators.

**Deliverable.** A working indicator extraction pipeline.

## Sprint 16 · Assessment Engine

**Objective.** Build a system that produces an abandonment index.

**Deliverable.** An assessment engine producing explainable abandonment indices.

---

# Block 6 · AI Experimentation

Compare approaches to validate the scientific methodology. Every experiment is
recorded in MLflow and its artefacts versioned with DVC.

## Sprint 17 · Zero-shot System

**Objective.** Build a pipeline with no training.

**Deliverable.** A working zero-shot pipeline with recorded results.

## Sprint 18 · Fine-Tuning

**Objective.** Train the model's final stage.

**Deliverable.** A fine-tuned model with a documented comparison.

## Sprint 19 · Scientific Comparison

**Objective.** Compare the expert system against the trained model.

**Deliverable.** A scientific comparison document with conclusions.

---

# Block 7 · Platform

Build the web interface that exposes the system's functionality.

## Sprint 20 · API

**Objective.** Implement the system's REST API.

**Deliverable.** A working, documented API, including the endpoint that takes a
bounding box and launches a run over that extent, and the endpoint that returns
its results.

## Sprint 21 · Frontend

**Objective.** Build the interactive web interface.

**Deliverable.** A working frontend connected to the API, on which the user
draws a bounding box on the map, launches the detection over that extent and
sees the results drawn back on it.

## Sprint 22 · Results

**Objective.** Visualise analysis results in the platform.

**Deliverable.** Complete result visualisation in the platform.

## Sprint 23 · Reports

**Objective.** Generate reports automatically.

**Deliverable.** A working report generation system.

> **Milestone: MVP (v1.0) complete at Sprint 23.**

---

# Block 8 · AI Agents and RAG

Evolve the system towards an agentic architecture with intelligent orchestration
and RAG-enriched report generation.

## Sprint 24 · LangGraph Orchestration

**Objective.** Refactor the pipeline as a graph of agents, where each stage
(download, processing, detection, assessment) becomes a node or tool.

**Deliverable.** The pipeline orchestrated by LangGraph.

## Sprint 25 · LlamaIndex RAG

**Objective.** Index technical documentation to enrich the system.

**Deliverable.** A working RAG system over indexed documentation.

## Sprint 26 · RAG-enriched Reports

**Objective.** Combine the report engine from Sprint 23 with the RAG system from
Sprint 25.

**Deliverable.** A report system enriched with RAG.

---

# Final Block · Optimisation

Cross-cutting work on performance, accuracy and scalability once the extended
version is complete.

---

## Related Documents

- [Next Tasks](next_tasks.md) — the active slice
- [Current State](current_state.md) — live status
- [Project Context](project_context.md) — scope and domain concepts
- [System Architecture](architecture/architecture.md)
- [ADR Index](architecture/adr/README.md)
