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
| **MVP (v1.0)** | Blocks 1–7 — a complete, defensible system for the thesis | 1–23 |
| **Extended (v2.0)** | Block 8 — agentic orchestration and RAG | 24–26 |
| **Optimisation** | Final block — performance, accuracy, scalability | — |

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
`pyproject.toml`, Docker, Docker Compose, DevContainer with GDAL/PDAL at system
level; Ruff (lint and format), strict MyPy, import-linter, Pytest, pre-commit; `tests/unit/` and `tests/acceptance/`;
`scripts/policy_guard.py` with its tests and its hook.

## Sprint 2 · Runtime Foundations

**Objective.** Prepare the project for maintainable execution.

**Deliverable.** Centralised configuration and logging in place, with no secret
read from anywhere but the environment.

Scope: logging, environment variables, centralised configuration.

## Sprint 3 · CI/CD

**Objective.** Automate the development process.

**Deliverable.** A working CI pipeline.

Scope: GitHub Actions running lint, formatting, type checking, tests and the
Docker build.

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

**Deliverable.** A working, documented API.

## Sprint 21 · Frontend

**Objective.** Build the interactive web interface.

**Deliverable.** A working frontend connected to the API.

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
