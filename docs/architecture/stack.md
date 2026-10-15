# Technology Stack

> Complete list of technologies, frameworks and tools used in the project.
> Entries annotated *deferred* or *conditional* stay on the list but are not in
> use in MVP 1.0; see [ADR-007](adr/adr-007-mvp-1-0-scope.md) and the status
> table in [roadmap.md](../roadmap.md).

## Backend

* Python 3.12
* uv (dependencies, environment, lockfile)
* FastAPI (MVP 1.0: a small documented endpoint set)

## AI / ML

* PyTorch
* YOLO11
* RT-DETR
* SAM2 (advanced, deferred)
* DINOv2 (advanced, deferred)

The detector actually used is selected in ADR-004 from the feasibility
evidence.

## GIS

* GeoPandas
* Rasterio
* GDAL (at system level in the container)
* PDAL (conditional — not installed; decided by ADR-004)
* Shapely

## Storage

* Files: GeoTIFF, GeoPackage, GeoParquet, GeoJSON
* Acquisition manifest with checksums, versioned in git

## Database

* PostgreSQL (deferred in MVP 1.0)
* PostGIS (deferred in MVP 1.0 — results are files until a query workload exists)

## Frontend

* React (deferred in MVP 1.0)
* MapLibre (MVP 1.0: one static map page)

## Infrastructure

* Docker
* Docker Compose
* Dev Containers

## Code Quality

* Ruff (linting and formatting)
* MyPy (strict)
* import-linter (layer boundaries)
* Pytest
* pre-commit

See [ADR-005](adr/adr-005-dependency-and-environment-manager.md).

## Observability

* Standard library `logging`, configured with `dictConfig`

See [ADR-006](adr/adr-006-logging-strategy.md).

## CI/CD

* GitHub Actions (MVP 1.0: one workflow running the quality gate)

## MLOps

* MLflow (MVP 1.0: local file store)
* DVC (deferred in MVP 1.0 — the acquisition manifest covers input traceability)

## v2.0 — Agentes y RAG

* LangGraph (deferred)
* LlamaIndex (deferred)
