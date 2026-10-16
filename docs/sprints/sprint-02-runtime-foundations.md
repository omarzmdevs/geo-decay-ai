# Sprint 02 · Runtime Foundations

## Block

Block 1 · Architecture and Infrastructure

## Goal

Prepare the project for maintainable execution: every runtime setting is read
from one validated, typed configuration object — the target bounding box
included — and every process configures logging once from it.

## Execution Mode

**Headless, from committed handoffs.** No deliverable of this sprint touches a
protected path, so each task runs as an autonomous developer session under the
allowlist written into its handoff. The exception is the feasibility
experiment, which is manual work by the user and the orchestrator and produces
no code.

## Requirements

* A `BoundingBox` value object in the domain layer: x-first axis order, strict
  extent validity, CRS in `AUTHORITY:CODE` form, standard library only.
  Protected by acceptance tests, because an axis swap produces results that look
  plausible and are wrong.
* A `Settings` object in the delivery layer reading the environment and `.env`
  under the `GEO_DECAY_` prefix, validated at construction, with the failing
  variable named in the error. No module-level singleton and no import-time
  environment read.
* `.env.example` declaring every variable, with placeholders only.
* Logging configured once per process from those settings, exactly as decided in
  [ADR-006](../architecture/adr/adr-006-logging-strategy.md): two formatters,
  one handler on standard output, no new dependency.
* The deterministic seed externalised as configuration (absorbed from Sprint 6,
  see Notes).
* The ADR-005 quality gate stays green, and the new dependency stays confined to
  the delivery layer.

## Prerequisites

* [ADR-003](../architecture/adr/adr-003-src-layout-and-layer-boundaries.md) —
  the layer boundaries that keep `pydantic-settings` out of the domain.
* [ADR-005](../architecture/adr/adr-005-dependency-and-environment-manager.md) —
  uv and the quality gate the deliverables must pass.
* [ADR-006](../architecture/adr/adr-006-logging-strategy.md) — the logging
  strategy handoff 008 implements. Recorded 2026-10-15.
* [ADR-007](../architecture/adr/adr-007-mvp-1-0-scope.md) — the executed scope,
  which adds the bounding-box variable to this sprint and absorbs Sprint 6 into
  it. Recorded 2026-10-15.
* Sprint 1 baseline, commit `52232d4`: skeleton, container with system GDAL,
  enforced quality gate, write-scope guard and commit hook.

## Tasks

Execution order: 007 (tester mode → user commit → implementation) → 008. Handoff
008 consumes the `Settings` object, so it does not start before 007 is ACCEPTED
and committed. The experiment runs in parallel and gates nothing in this sprint.

- [x] [007](../prompts/007-bounding-box-and-configuration.md) — tester mode:
      `tests/acceptance/test_bounding_box_contract.py`, failing. Headless.
- [x] User: commit the failing acceptance tests. That commit is the proof they
      were red before the implementation existed.
- [x] [007](../prompts/007-bounding-box-and-configuration.md) — implementation:
      `BoundingBox`, `Settings`, unit tests, `.env.example`, and
      `pydantic-settings` added to the lockfile. Headless.
- [x] Orchestrator: verify 007 against its criteria, re-run the gate, append the
      `## Verification` section; then run the documenter and hand the diff to
      the user.
- [ ] [008](../prompts/008-logging-configuration.md) — implementation:
      `configure_logging` and its unit test. Headless.
- [ ] Orchestrator: verify 008, then documenter, then user commit.
- [ ] User: supply the bounding box to study, as four coordinates and their CRS.
      It unblocks the experiment, not the sprint.
- [ ] User and orchestrator: run the feasibility measurement recorded in
      [exp-001](../experiments/exp-001-data-feasibility.md) and draft ADR-004
      from it. Required before Sprint 8; may close after this sprint does.
- [ ] Sprint close: update `current_state.md` and `next_tasks.md`, fill the
      dates and the handoff verdicts here, and move this sprint to complete in
      the directory index.

## Deliverable

Centralised configuration and logging in place, with no secret read from
anywhere but the environment, and the covered extent selected without touching
code.

## Handoffs Executed

<!-- Verdicts are transcribed here as each handoff is verified. -->

- [007 · Bounding box and centralised configuration](../prompts/007-bounding-box-and-configuration.md) — ACCEPTED 2026-10-16, full gate green (167 tests)
- [008 · Logging configuration](../prompts/008-logging-configuration.md) — PENDING

## Notes

- **`pydantic-settings` is the sprint's only new runtime dependency.** The
  deliverable is configuration *validated at start-up*, and hand-rolling
  parsing, type coercion, `.env` loading and error messages is more code to own
  than the dependency. It is confined to the delivery layer, so the import
  contracts keep it out of the domain.
- **Acceptance tests cover the bounding box only.** It is a data contract whose
  failure mode is silent. Logging configuration is declarative work against a
  decided design and carries unit tests only.
- **Sprint 6 is absorbed here** ([ADR-007](../architecture/adr/adr-007-mvp-1-0-scope.md)):
  the environment is already fixed by the lockfile and the container, and
  externalised configuration is this sprint's deliverable. The remaining piece,
  determinism, enters as the `GEO_DECAY_RANDOM_SEED` variable declared in
  handoff 007. No seeding function is written: nothing in the project is random
  yet, and ADR-007 forbids building a component before the sprint that first
  needs it. Applying the seed belongs to the first sprint that trains or
  samples.
- **Nothing calls `configure_logging` yet.** There is no entry point until
  Sprints 20 and 21; handoff 008 wires the function and deliberately leaves the
  call site to them.
- **The bounding box is held as configuration, not as an argument**, so the
  same value is later filled by the CLI, by the API endpoint of Sprint 20 and by
  the map selection of Sprint 21 without changing the layers below.
- **Deviation from the lifecycle, recorded deliberately.** This log was created
  after the sprint's handoffs were written, not at sprint start. `AGENTS.md`
  → Task Lifecycle names only the handoffs in its planning step, which is where
  the omission came from; the obligation is stated in
  `.agents/roles/orchestrator.md`. Writing the log is what surfaced the absorbed
  Sprint 6 requirement above, which the two handoffs did not cover.

## Documents Updated

<!-- Completed as the sprint runs. -->

- [docs/sprints/README.md](README.md) — directory index
- [docs/next_tasks.md](../next_tasks.md)
- [docs/current_state.md](../current_state.md) — documenter, 007 verdict recorded
- [docs/prompts/007-bounding-box-and-configuration.md](../prompts/007-bounding-box-and-configuration.md) — `GEO_DECAY_RANDOM_SEED` added
- [docs/experiments/exp-001-data-feasibility.md](../experiments/exp-001-data-feasibility.md) — PENDING, blocked on the bounding box

## Date Started

2026-10-15

## Date Completed

<!-- YYYY-MM-DD -->
