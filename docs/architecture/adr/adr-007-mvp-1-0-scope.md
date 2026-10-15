# ADR-007: MVP 1.0 Scope

## Status

Accepted

## Date

2026-10-15

Amends [ADR-002](adr-002-operational-roadmap.md), which fixed the plan at
twenty-six sprints across eight blocks. The structure and the numbering are
unchanged; this record says which sprints are executed now and which are
reduced or deferred.

## Context

The plan builds the system strictly layer by layer: all MLOps infrastructure
before any data, the whole GIS core before any detection, the platform at the
end. Reviewing it against what the project is for exposed four problems.

**Effort is distributed away from the core.** The sprints producing the
project's distinctive output — detection, indicators, the abandonment index and
the comparative experiment — are nine of twenty-six, preceded by thirteen
sprints of infrastructure, none validated against real data.

**Several components are built before anything consumes them.** Experiment
tracking and data versioning are configured with no experiment to record and no
dataset to version. A spatial database is introduced in the GIS core although
nothing issues a spatial query until the platform. The platform itself is four
sprints, three of them frontend work.

**The largest uncertainty is scheduled last.** Nothing verifies that the
available imagery and elevation data support the intended indicators —
resolution, temporal coverage, product availability for an extent — until the
sprint that implements those indicators. That assumption carries the whole
assessment stage and is tested after everything has been built on it.

**The project has one developer.** Total effort has a ceiling, so breadth is
paid for out of the core rather than added to the plan.

## Decision

**MVP 1.0 is the executed subset of the existing plan.** Sprint numbering and
block structure stay as they are; the per-sprint status table lives in
[roadmap.md](../../roadmap.md), which remains the operational source of truth.
Deferred entries stay on record and nothing is planned or launched from them.

Four decisions give the reduction its shape.

**The feasibility evidence comes first.** Before Sprint 8, an experiment
measures what the data supports for one bounding box, and ADR-004 is written
from it: CRS, tiling, inter-stage data contracts, the elevation route and the
detection strategy. It touches no code, so it runs alongside Sprint 2 and
removes the largest unknown before anything is built against it. It also
replaces the Sprint 11 benchmark as the basis for choosing a detector.

**Nothing is built before it has a consumer.** MLflow is reduced to a local
file store. Data versioning is reduced to an acquisition manifest with
checksums, which is what traceability of inputs actually requires here. The
spatial database is deferred in favour of files, which the pipeline reads and
QGIS opens directly.

**Dependent work degrades instead of blocking.** Indicators are a pluggable
collection and the assessment engine consumes whichever are available,
recording the rest as absent. A data route that needs tooling the project does
not have therefore costs one indicator group, not the pipeline. Two items are
conditional on this basis: system-level PDAL in Sprint 9 and the fine-tuning
arm of Sprint 18.

**Traceability is not reduced.** The reduction removes breadth, not rigour.
Experiments in MLflow and in the experiment records, acquired data in the
manifest, indicator availability in the assessment output, technical decisions
in ADRs and task execution in the run records all stay as they are.

**The bounding box is a configuration variable.** The extent covered by
detection is selected without touching code, which keeps the unit of work
explicit and makes the feasibility experiment repeatable on another extent.
Scaling beyond a single bounding box stays in the deferred optimisation block.

## Alternatives Considered

**Keep the full plan and go faster.** Rejected: the constraint is total effort,
not pace, so this only reduces the time available per sprint, and the core
sprints are the ones that suffer.

**Reduce the quality gate instead of the breadth.** Dropping strict typing,
layer contracts or acceptance tests would free effort everywhere. Rejected: the
gate is cheap to keep once built and is what makes the result trustworthy.
Breadth is the expensive part and the one with the least return.

**Keep the MLOps block intact.** Configuring tracking and versioning up front
means everything is recorded from the first downloaded file. Rejected in full
and kept in its useful part: tracking stays in Sprint 4 but reduced, and the
acquisition manifest gives input traceability without a versioning system.

**Keep PostGIS.** The right answer with concurrent clients or large query
workloads. Rejected here: one process, one developer, data that fits in files,
and files are inspectable in QGIS without a running service.

**Reduce scope later, if needed.** Rejected: an unreduced plan spends effort on
infrastructure early, so by the time the shortfall is visible the effort has
gone to the wrong part.

## Consequences

**Positive.** The core sprints hold the largest share of the effort. The main
unknown is tested before anything depends on it. Each stage writes files with a
documented contract, so any stage can be inspected without running the next.
Fewer moving parts to operate: no database service, no versioning system, no
separate frontend project. Everything delivered in Sprint 1 is reused
unchanged, and the plan's structure is preserved, so a deferred item can be
picked up later without re-planning.

**Negative.** File-based results mean no concurrent access and no large-area
queries; introducing a database later is a migration. Without DVC, data lineage
rests on the manifest and on discipline rather than on a tool. Choosing the
detector from feasibility evidence rather than a measured benchmark is a weaker
justification for that choice. The conditional items mean the delivered
indicator set is not known in advance; the assessment engine is built to make
that acceptable, and the gaps are recorded rather than hidden.

## Related

- [ADR-002](adr-002-operational-roadmap.md) — the plan this one amends
- [ADR-006](adr-006-logging-strategy.md) — Sprint 2 logging decision
- **ADR-004** — pending; CRS, tiling, data contracts, elevation route and
  detection strategy, written from the feasibility experiment
- [Roadmap](../../roadmap.md) — the per-sprint status table
