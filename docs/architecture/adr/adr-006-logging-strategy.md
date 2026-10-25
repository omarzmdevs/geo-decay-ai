# ADR-006: Logging Strategy

## Status

Accepted

## Date

2026-10-15

## Context

Sprint 2 adds logging, under three constraints the project already has.

**The libraries decide the substrate.** Rasterio, Fiona, pyproj, GeoPandas,
PyTorch, MLflow and Uvicorn all emit through the standard library's `logging`.
Any solution either sits on top of that machinery or runs beside it, in which
case library diagnostics are lost or need a bridge.

**Layer boundaries forbid casual coupling.** ADR-003 keeps the four layers
independent and enforces it with import-linter. A logging facility imported by
every layer is a new import edge the contracts must permit, and a third-party
logging API called from every module couples the codebase to that vendor.

**Runtime logs are not the experiment record.** Logging answers *what the
process did and where it failed*; metrics, parameters and artefacts belong to
MLflow and to the experiment records. Conflating them produces a logging system
that is rewritten as soon as real experiments start.

## Decision

**Call sites use the standard library directly:** `logging.getLogger(__name__)`.
Nothing project-specific is imported in order to log, so no new import edge
crosses a layer boundary and no layer depends on a logging vendor.

**Configuration is centralised and declarative.** A single `configure_logging`
function applies `logging.config.dictConfig` built from the centralised
configuration of Sprint 2, called once at start-up by each delivery entry point,
which is the composition root. No other layer configures logging and no module
configures it at import time.

**Two formatters, selected by configuration:** human-readable for interactive
development, one JSON line per record for container and CI output. Level,
format and per-logger overrides — in particular silencing noisier third-party
loggers — come from configuration, never from code.

**No log file management.** Records go to standard output; collection, rotation
and retention belong to whatever runs the process.

**Structured context is deferred.** Binding a run or tile identifier onto every
record has no consumer before the tiling pipeline exists. Because call sites use
the standard library, it can be added later without touching them: a
`logging.Filter` backed by `contextvars`, or structlog in its standard-library
integration mode, where `ProcessorFormatter` processes records emitted by
`logging.getLogger`. Revisited in the sprint that first needs it.

## Alternatives Considered

**structlog from the start.** The strongest option on the merits: processor
pipelines, native JSON, context binding through `contextvars`. Rejected on
timing only — its distinctive value has no consumer yet, and adopting it later
costs nothing because the integration is configuration-side.

**loguru.** The most ergonomic API of the three. Rejected on two counts: it is a
parallel system, so Rasterio, PyTorch and Uvicorn reach it only through an
`InterceptHandler` bridge; and it is called by name at every call site, coupling
every layer to a third-party API in a codebase whose layer independence is
enforced in the gate.

**A project-specific `get_logger` wrapper.** Rejected: it adds an import edge
from every layer to a shared module in order to wrap `logging.getLogger` and
return its object. The standard library is already the abstraction.

**A custom logging facility** — own levels, multi-sink router, rotation policy.
Rejected: reimplements the standard library and the container runtime.

## Consequences

**Positive.** No runtime dependency added. Third-party diagnostics appear in the
same stream and format as the project's own. Call sites are vendor-neutral, so
the structured-logging decision stays open at zero migration cost. Behaviour
changes per environment through configuration, without touching code.

**Negative.** `dictConfig` is verbose and fails at start-up on a malformed
dictionary — the right moment, but not self-explanatory. Silencing noisy
third-party loggers requires knowing their names, found by observation. Without
context binding, correlating records across a tile run depends on what each
message carries; accepted until the deferral above is revisited.

## Related

- [ADR-003](adr-003-src-layout-and-layer-boundaries.md) — the layer boundaries
  the call-site decision protects
- [Roadmap](../../roadmap.md) — Sprint 2 (this decision), Sprint 4 (MLflow, the
  experiment record this is kept separate from)
