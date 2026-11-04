# Sprint 5 · Feasibility Instrumentation

## Block

Block 3 · GIS Core — as its gate rather than as part of it. The sprint produces
no production code: it instruments the measurement that ADR-004 is written from,
and ADR-004 is what unblocks Sprints 8 to 10.

It occupies **slot 5**, left free in MVP 1.0 by the deferral of Sprint 5 · DVC.
DVC stays deferred; the number is reused so execution order and sprint number
keep matching, and the reuse is recorded as an amendment to
[ADR-007](../architecture/adr/adr-007-mvp-1-0-scope.md).

## Goal

Make [EXP-001](../experiments/exp-001-data-feasibility.md) measurable, and
re-measurable by a third party, with one notebook the user runs on their own
machine: an interactive map on which to draw the study extent, PNOA epoch
availability and image quality, cadastral footprints and their attributes, an
elevation availability probe, example buildings across epochs, and an empty
labelling table for the manual pass.

## Execution Mode

Headless for both handoffs: neither touches a protected path. Two consequences
of the sandbox shape the acceptance criteria, and are not defects:

- **No network.** The agent sandbox is not given the IGN, CNIG or Catastro
  domains (decision of 2026-11-04). Every criterion is therefore offline, and
  "the notebook runs to completion with every request failing" is a criterion
  rather than a problem: it is what proves the missing-data policy works.
- **The measurement is the user's run.** The agent delivers instrumentation; the
  figures come from the user executing it. That is what makes the experiment
  auditable by someone who is not an agent.

## Requirements

1. One helper module, `notebooks/eda_helpers.py`, outside `src/` and outside the
   ADR-003 layer contracts, importable from a notebook with no path
   manipulation and no `geo_decay_*` import.
2. Provider definitions as **data**: one dictionary entry per provider, holding
   endpoints, layer names, advertised CRS, the per-epoch layer pattern and the
   expected vector attribute names. Nothing Spain-specific inside a function.
3. Every request recorded in `data/interim/exp-001/manifest.csv` with URL, UTC
   timestamp, HTTP status, byte count and MD5, and its body saved beside it.
4. Every network failure recorded and returned, never raised: a refused host
   produces an `ABSENT` row, not a traceback.
5. One notebook, `notebooks/01-pnoa-catastro-eda.ipynb`, in which **every code
   cell is preceded by a markdown cell** explaining what that step does, why,
   and what to look at in its output.
6. All parameters — extent, CRS, provider key, year range, request size, output
   directory — in the first code cell, and nowhere else.
7. An `eda` dependency group that the default `uv sync` does not install.
8. The extent is a **required parameter with no default**: step 1 of EXP-001 is
   still open, so neither handoff may bake a bounding box into code, a test or a
   notebook cell.
9. An **interactive map selector** in the notebook: draw a rectangle, read back
   width, height, area, geodesic figures, the projection skew, the snapped
   extent, its pixel size and its tile count, and the two `GEO_DECAY_*` lines.
   The projection and snapping arithmetic lives in the helper module, where it
   is checked offline against exact expected values; only the widget is in the
   notebook.

## Prerequisites

- `notebooks/**` in the developer write scope of `.agents/policy.yaml` —
  **done by the user on 2026-11-04.**
- The launch command adds `Bash(uv sync*)` and `Bash(uv lock*)`: both handoffs
  change dependencies.
- The data domains are **not** added to the sandbox allowlist, by decision. Any
  criterion that would need them is wrong by construction.

## Tasks

- [ ] [013 · EDA helper module and provider configuration](../prompts/013-eda-toolkit-and-provider-config.md)
- [ ] [014 · The exploratory analysis notebook](../prompts/014-eda-notebook.md)
- [ ] The user draws the extent on the map and records it in EXP-001 →
      Configuration from the lines the notebook prints
- [ ] The user runs the notebook and commits it with its outputs
- [ ] The user completes the manual labelling pass (EXP-001 step 6) from the
      table the notebook writes
- [ ] Orchestrator: EXP-001 Analysis and Conclusion from the measured figures
- [ ] Orchestrator: draft ADR-004
- [ ] Orchestrator: `docs/research/feasibility-assessment-exp-001.md` and
      `docs/research/infrastructure-status-2026-11.md`

## Deliverable

A notebook that anyone can run to reproduce every figure in EXP-001 → Results,
and that degrades to a complete, readable "absent" report with no network at
all. ADR-004 is **not** part of this sprint's deliverable: the sprint closes
when the measurement exists and is recorded.

## Handoffs Executed

<!-- Filled by the documenter as each handoff is verified -->

## Notes

**The extent is still open, and the sprint gives you the means to close it.**
EXP-001 step 1 has no value yet, and no agent chooses one: the notebook opens a
map, you draw the rectangle, and it reports what you drew in the terms ADR-004
will need — metres, area, skew against the projected CRS, whole-tile fit. That
is also the cheapest form of the portability requirement: an instrument that
cannot hard-code an extent cannot hard-code a country either, and the map's own
opening view comes from the provider entry rather than from a notebook cell.

**Why exploratory code is allowed here at all.** ADR-007's rule is that nothing
is built before the sprint that first needs it, and the acquisition layer is
Sprint 8. The rule holds: nothing in this sprint is production code, none of it
sits under `src/`, none of it is reachable from the CLI, and Sprint 8 is free to
discard all of it. What Sprint 8 inherits is the measured evidence and the
portability constraints recorded in EXP-001, not the module.

## Documents Updated

<!-- Filled by the documenter -->

## Date Started

2026-11-04

## Date Completed

<!-- YYYY-MM-DD -->
