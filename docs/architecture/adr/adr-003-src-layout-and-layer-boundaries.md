# ADR-003: `src/` Layout and Layer Boundaries

## Status

Accepted

## Date

2026-10-08

## Context

[architecture.md](../architecture.md) defines four layers — domain, data,
application, delivery — and requires that business logic never depends on
delivery. Sprint 1 creates the folder structure and `pyproject.toml`, so the
layout must be fixed before any code exists: moving packages later means
rewriting every import, test path and tool configuration.

Two constraints shape the decision:

- **Boundaries must be enforced, not documented.** Code is written by agents
  working from small contexts; a rule that only lives in prose will be broken
  without anyone noticing until review.
- **The domain must stay free of I/O and heavy dependencies**, so that the
  abandonment index and the data contracts can be unit-tested without GDAL,
  PDAL, a database or a GPU.

## Decision

**One distribution, four top-level import packages under `src/`**, one per
layer, sharing the `geo_decay_` prefix:

```
src/
├── geo_decay_domain/        # entities, indicators, abandonment index, data
│                            # contracts, ports (typing.Protocol). No I/O.
├── geo_decay_data/          # PNOA/LiDAR acquisition, GIS processing, tiling,
│                            # PostGIS persistence: implements domain ports
├── geo_decay_application/   # use cases: detect, assess, report
└── geo_decay_delivery/      # composition root
    ├── api/                 # FastAPI
    └── cli/
tests/
├── unit/                    # mirrors src/: unit/domain, unit/data, ...
└── acceptance/              # owned by tester mode
scripts/                     # standalone tooling, not packaged
```

Each package ships a `py.typed` marker. A single `pyproject.toml` at the
repository root declares the distribution (`geo-decay`) and all four packages.

**Dependency direction (dependency inversion).** Ports are defined in the
domain as `typing.Protocol` classes. The application layer depends only on the
domain and orchestrates data through those ports; the data layer implements
them. Delivery is the composition root: it is the only layer that imports both
application and data, and it wires concrete adapters into use cases.

```
geo_decay_delivery
   ├──▶ geo_decay_application ──┐
   └──▶ geo_decay_data ─────────┼──▶ geo_decay_domain
```

This refines the layer table in `architecture.md`, where the application
"orchestrates domain and data": it does so through ports, never by importing
the data layer.

**Enforcement: import-linter contracts in the quality gate.** Declared in
`pyproject.toml` (`[tool.importlinter]`) and run as `lint-imports` by the gate
and by pre-commit:

1. **Layers** — `geo_decay_delivery` above `geo_decay_application` and
   `geo_decay_data`, both above `geo_decay_domain`. No layer imports one above it.
2. **Independence** — `geo_decay_application` and `geo_decay_data` never import
   each other.
3. **Forbidden (domain purity)** — `geo_decay_domain` imports no I/O, framework or
   heavy library: at least `osgeo`, `rasterio`, `pdal`, `geopandas`, `fiona`,
   `sqlalchemy`, `psycopg`, `fastapi`, `torch`, `ultralytics`, `mlflow`, `dvc`.
   Which pure libraries the domain may use (geometry, validation) is decided by
   ADR-004 together with the data contracts.
4. **Forbidden (delivery frameworks)** — `geo_decay_application` and
   `geo_decay_data` never import `fastapi` or the CLI framework.

Ruff complements this with `flake8-tidy-imports` (TID252): relative imports
that cross a package boundary are banned, so every cross-layer import is
absolute and visible to import-linter.

## Alternatives Considered

**One package with a subpackage per layer** (`geo_decay/domain`, ...).
Equivalent for import-linter and slightly less verbose. Rejected in favour of
top-level packages: a layer is a visibly separate unit in the tree, in imports
and in coverage reports, and the layout can later become a uv workspace (one
distribution per layer) without renaming any import.

**Layers inside each bounded context** (`acquisition/`, `detection/`,
`assessment/`, each with its own layers). Scales better with many contexts, but
requires fixing the contexts now, before ADR-004 has defined the data contracts
between stages. Can be adopted inside a layer later if a layer grows too large.

**A uv workspace with one `pyproject.toml` per layer.** Gives real dependency
isolation: the domain's manifest cannot even declare rasterio. Rejected for now:
four manifests, four dependency sets and cross-member version management cost
more than they protect while import-linter already forbids the imports. The
chosen layout migrates to it without import changes.

**Ruff `banned-api` (TID251) instead of import-linter.** No new dependency, but
the ban list is global, layer exceptions need per-directory configuration that
disables the rule wholesale, and transitive imports (domain → x → data) are not
detected. Rejected.

**Convention and review only.** Rejected: see the first constraint.

## Consequences

**Positive.** Layer violations fail the gate before review, including indirect
ones. The domain is testable without GIS libraries, which also keeps its unit
tests fast and runnable outside the container. Ports make adapters (PostGIS,
filesystem, MLflow) replaceable in tests by in-memory fakes.

**Negative.** Four top-level names instead of one, and longer imports
(`from geo_decay_domain.index import ...`). Every new external library that
does I/O must be added to the domain's forbidden list, or the purity contract
silently weakens; the developer role adds it when introducing the dependency,
and verification checks it. Ports add indirection that a script-style pipeline
would not need.

**Follow-ups.** ADR-004 fixes which pure libraries the domain may use and the
data contracts between stages. The CLI framework, once chosen, is added to
contract 4.

## Related

- [Architecture](../architecture.md), [Stack](../stack.md)
- [ADR-005](adr-005-dependency-and-environment-manager.md) — dependency manager
  and quality-gate tooling
- [Sprint 01 log](../../sprints/sprint-01-foundations.md)
