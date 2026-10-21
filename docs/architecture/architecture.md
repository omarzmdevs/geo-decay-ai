# System Architecture

> High-level architecture of the system. Updated whenever architectural changes are made.

## Overview

The system is a pipeline exposed through a web platform. Given a bounding box, it
downloads PNOA orthophotos and LiDAR point clouds, prepares and tiles them,
detects infrastructure, extracts indicators for each detection and combines them
into an abandonment index, which the platform shows on a map and summarises in a
generated report.

Four layers, kept independent so that business logic never depends on delivery:

| Layer | Responsibility |
|---|---|
| **Domain** | Abandonment indicators and index, detection and tile entities, data contracts. No I/O. |
| **Data** | PNOA and LiDAR acquisition, GIS processing, tiling, persistence (MVP 1.0: files; PostGIS deferred). |
| **Application** | Detection, indicator extraction, assessment and report generation (deferred), orchestrating domain and data. |
| **Delivery** | FastAPI, the map frontend (MVP 1.0: one MapLibre page; React deferred) and the CLI. Interchangeable. |

Each layer is a top-level package under `src/` (`geo_decay_domain`,
`geo_decay_data`, `geo_decay_application`, `geo_decay_delivery`). Ports are
defined in the domain; the application uses them and the data layer implements
them, so application and data never import each other. Delivery is the
composition root: it holds the validated settings object that every runtime
value comes from — the target bounding box included — and configures logging
once at start-up from it, so no layer below reads the environment
([ADR-006](adr/adr-006-logging-strategy.md), Sprint 2). import-linter enforces
these rules in the quality gate
([ADR-003](adr/adr-003-src-layout-and-layer-boundaries.md)).

MLflow and DVC (deferred) sit alongside the pipeline rather than inside it:
they record experiments and version data and artefacts without the pipeline
depending on them. The build order of these layers is the block order in
[roadmap.md](../roadmap.md): infrastructure, then MLOps, then the GIS core, then
detection, assessment, experimentation and the platform. Which sprints are
executed in MVP 1.0, and which are reduced or deferred, is the status table in
that same file ([ADR-007](adr/adr-007-mvp-1-0-scope.md)).

Two invariants hold across the layers. **Every stage writes files with a
documented contract**, so each one can be run and inspected in QGIS or a
notebook without the stage that follows it. **Indicators are a pluggable
collection**: the assessment engine consumes whichever were computable and
records the rest as absent with the reason, so an unavailable input removes one
indicator group instead of blocking the pipeline.

## Component Diagram

### MVP (v1.0) Architecture

In MVP 1.0 the PostGIS node is replaced by files, the frontend is a single
MapLibre page and report generation is deferred.

```mermaid
graph TD
    User([User]) --> Frontend[Frontend React + MapLibre]
    Frontend --> API[API FastAPI]
    API --> Download[PNOA & LiDAR Download]
    API --> GIS[GIS Processing & Tiles]
    API --> Detect[Infrastructure Detection]
    API --> Assess[Abandonment Assessment]
    API --> DB[(PostGIS)]
    API --> Report[LLM Report Gen]
    
    %% MLOps affects training/experimentation tracking mostly, but is foundational
    MLOps[MLOps: MLflow + DVC] -.-> Detect
    MLOps -.-> Assess
```

### Extended Version (v2.0) Architecture

```mermaid
graph TD
    User([User]) --> Frontend[Frontend React + MapLibre]
    Frontend --> API[API FastAPI]
    API --> Agent[LangGraph AI Agent]
    
    Agent --> Download[PNOA & LiDAR Download]
    Agent --> GIS[GIS Processing & Tiles]
    Agent --> Detect[Infrastructure Detection]
    Agent --> Assess[Abandonment Assessment]
    Agent --> DB[(PostGIS)]
    Agent --> RAG[LlamaIndex RAG]
    Agent --> Report[LLM Report Gen]
    
    RAG -.-> Docs[(Technical Docs & Urban Law)]
```

## Data Flow

1. **Request.** A bounding box arrives from the configuration variable that
   holds the extent to cover, from the CLI, or from the map, where the user
   draws it and the frontend posts it to the API. All three fill the same
   four coordinates and CRS.
2. **Acquisition.** Orthophotos and LiDAR tiles are downloaded for that extent
   and versioned on arrival, so every later result traces back to a known input.
3. **Preparation.** Rasters and point clouds are processed into analysis-ready
   data, and the area is split into fixed-size tiles for parallel work.
4. **Detection.** Each tile is run through the selected detection methodology,
   and every detection becomes an independent geospatial entity in PostGIS.
5. **Assessment.** For each entity, indicators are extracted — vegetation, roof
   condition, debris, accessibility, temporal change and LiDAR-derived features —
   and combined into an explainable abandonment index, accompanied by the
   per-indicator contributions and by the groups that were unavailable.
6. **Delivery.** Entities and indices are served through the API, shown on the
   map and summarised in generated reports.

Heavy data never travels through an agent's context: it is written to disk,
versioned, and inspected through scripts whose output is read instead.

## Key Design Decisions

Recorded:

- [ADR-001](adr/adr-001-agent-governance.md) — agent governance model: roles,
  tiers, security layers.
- [ADR-002](adr/adr-002-operational-roadmap.md) — operational roadmap and the
  composition of Block 1.
- [ADR-003](adr/adr-003-src-layout-and-layer-boundaries.md) — `src/` layout and
  the enforced boundaries between the four layers above.
- [ADR-005](adr/adr-005-dependency-and-environment-manager.md) — uv, Python
  3.12 and the quality-gate tooling.
- [ADR-006](adr/adr-006-logging-strategy.md) — logging on the standard library,
  configured declaratively in the composition root.
- [ADR-007](adr/adr-007-mvp-1-0-scope.md) — MVP 1.0 scope: what is executed
  now, what is reduced or deferred, and why.

Pending:

- **ADR-004** — coordinate reference system, tile size and the data contracts
  between pipeline stages, plus the elevation route and the detection strategy.
  The decision most expensive to change later; produced from the feasibility
  experiment and required before the GIS core (Block 3).

## Deployment Architecture

Development and execution both run in containers, so the C-level GIS dependencies
(GDAL, PDAL, Rasterio) are identical everywhere:

- A **DevContainer** provides the development environment, with GDAL installed
  at system level. PDAL is not installed; whether it is needed is decided by
  ADR-004.
- **Docker Compose** composes the application image with PostgreSQL/PostGIS
  (deferred in MVP 1.0) and the MLflow tracking server (MVP 1.0: a local file
  store, no server).
- **CI** runs the quality gate — lint, formatting, type checks, tests — on
  every push, through the same `.pre-commit-config.yaml` the commit hook uses
  (Sprint 3). It does not build the image: that is deferred while the
  DevContainer builds it daily ([ADR-007](adr/adr-007-mvp-1-0-scope.md),
  amendment 2026-10-21).

Secrets are supplied through the environment and never committed; `.env.example`
holds key names and placeholders only.

## Related Documents

- [Technology Stack](stack.md)
- [ADR Index](adr/README.md)
- [Project Context](../project_context.md)
