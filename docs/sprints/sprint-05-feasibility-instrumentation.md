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

Headless for handoffs 013 and 014: neither touches a protected path. **Handoff
015 is never headless** — it is interactive by design, one step per session,
because the map needs a person between two cells and because each step is
confirmed against the live services, which the agent sandbox cannot reach. Two
consequences of the sandbox shape the acceptance criteria, and are not defects:

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

- [x] [013 · EDA helper module and provider configuration](../prompts/013-eda-toolkit-and-provider-config.md)
- [x] [014 · The exploratory analysis notebook](../prompts/014-eda-notebook.md) — ACCEPTED; its deliverable was later discarded by the user and is
      superseded by 015
- [ ] [015 · The EDA notebook, one section at a time](../prompts/015-eda-notebook-step-by-step.md) — in progress, one step per
      session, tracked by the checkboxes inside the handoff:
  - [x] 0 · The self-contained folder — ACCEPTED 2026-11-04
  - [x] 1 · Section 4 · Provider capabilities — ACCEPTED 2026-11-05
  - [x] 2 · Sections 5 and 6 · Epoch availability and image quality — ACCEPTED 2026-11-06
  - [ ] 3 · Section 7 · Spectral check
  - [ ] 4 · Section 8 · Cadastral footprints
  - [ ] 5 · Section 9 · Elevation availability
  - [ ] 6 · Sections 10 and 11 · Example buildings and the labelling table
  - [ ] 7 · Section 12 · Findings
  - [ ] 8 · Close
- [x] The user draws the extent on the map and records it in EXP-001 →
      Configuration from the lines the notebook prints — drawn 2026-11-04 and
      committed as `notebooks/exp-001/out/extent.json`; transcribed into
      EXP-001 → Configuration by the documenter on 2026-11-05
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

- 013 · EDA helper module and provider configuration — ACCEPTED 2026-11-04
  ([handoff](../prompts/013-eda-toolkit-and-provider-config.md)); run as a
  `TIER_STANDARD` subagent launched from the orchestrator session.
- 014 · The exploratory analysis notebook — ACCEPTED 2026-11-04
  ([handoff](../prompts/014-eda-notebook.md)); run as a `TIER_DEEP` subagent.
  Twelve sections delivered and verified offline. The deliverable was
  **discarded by the user on 2026-11-04**, after the first live run showed the
  extent selector did not work; the verification record stands, the artefact
  does not.
- 015 · The EDA notebook, one section at a time — IN PROGRESS
  ([handoff](../prompts/015-eda-notebook-step-by-step.md)); interactive, never
  headless, one step per session. Three of its nine steps are closed:
  - **Step 0 · The self-contained folder — ACCEPTED 2026-11-04.** It settles
    nothing about the services: `eda.py` and `README.md` were created inside
    `notebooks/exp-001/`, the notebook reaches its last cell offline with
    `ABSENT:` rows, and nothing is written under `data/`. The `PROVIDERS` entry
    was copied unchanged, so every claim it makes stood unverified after it.
  - **Step 1 · Section 4 · Provider capabilities — ACCEPTED 2026-11-05**, from
    a live run by the user on 2026-11-04 (restore point `25b58f0`, work landed
    in `339ea81`). **4 of 4 services answered**, over five capability documents
    committed under `out/capabilities/` with five `manifest.csv` rows, all
    status 200: **26 CRS** in the union, **56 advertised layers**, **5 stored
    queries**, and **3 contradictions over 14 claim rows**. All four CRS the
    provider entry claims are advertised, and so is the extent's own
    `EPSG:25830`. The epoch range served is `PNOA2004`–`PNOA2024`. Of the three
    contradictions, two are real contradictions of the entry — the buildings
    layer and the stored query — and the third was the notebook's own
    `YEAR_LAST`, corrected in the step. Figures transcribed into
    [EXP-001](../experiments/exp-001-data-feasibility.md) → Results.
  - **Step 2 · Sections 5 and 6 · Epoch availability and image quality —
    ACCEPTED 2026-11-06**, from a live run by the user on 2026-11-06, who
    committed the notebook with its outputs. **9 of the 21 years return imagery**
    over the extent (2006–2023); the others answer with a blank image, which
    means the mosaic has no pixels there, not that the layer is missing. **Six of
    the nine present years measure 0.25 m/px**, confirming by measurement the
    `default_gsd_m` the provider entry assumed; 2006 is a bound (**≥ 0.5 m/px**)
    and 2012 and 2015 give no figure. A 10 m building occupies **40 × 40 px**.
    Quality flags: 12 of 21 epochs blank, 12 low-contrast, none saturated.
    **The usable series is about 7 epochs, not 21.** Section 6.2 was added
    afterwards, and the ladder table is now written to `out/ladder.csv`, with
    figures kept out of the notebook. Figures transcribed into
    [EXP-001](../experiments/exp-001-data-feasibility.md) → Results.

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

**Why the notebook was restarted, and what changed in how it is built.**
Handoff 014 delivered twelve sections in one run and every offline criterion
passed. The first run against the live services then showed that the section
everything else depends on — the map that chooses the extent — did not work, and
it took three separate causes to explain it: the resolution cell being run
before anything was drawn, a kernel restart losing the drawing while the cell
deleted the extent it had already recorded, and a confirmation written into a
widget that silently swallowed both the text and the exception. The sections
below it were therefore verified against nothing but their own absence
handling.

The lesson is not that the work was bad; it is that **offline verification
proves a notebook does not crash, and cannot prove it measures anything**.
Handoff 015 is built around that: one section per session, each one confirmed
against a live service by the user before the next is written, with the
checkboxes and per-step records kept inside the handoff. It is the first handoff
in this project that is deliberately not executable in one go.

Two decisions of the user's shape it. The experiment is **self-contained** in
`notebooks/exp-001/`, data included, so nothing of it leaks into `data/` and the
folder can be moved whole; small audit artefacts are versioned, imagery is not.
And **no measured fact is inherited** from the discarded case: the provider
entry starts from the committed values of handoff 013 and the first live run
settles them again. The cost of that is recorded honestly — the elevation
endpoint went with the revert, so EXP-001 question 2 has no instrument until an
endpoint is added, which is EDA-ELEV.

## Documents Updated

- [sprint-05 log](sprint-05-feasibility-instrumentation.md) — created by the orchestrator at sprint start; tasks and handoffs recorded by the documenter.
- [013 · EDA helper module and provider configuration](../prompts/013-eda-toolkit-and-provider-config.md) — handoff with Run Record and Verification (ACCEPTED 2026-11-04).
- [014 · The exploratory analysis notebook](../prompts/014-eda-notebook.md) — handoff with Run Record and Verification (ACCEPTED 2026-11-04); deliverable discarded by the user the same day.
- [015 · The EDA notebook, one section at a time](../prompts/015-eda-notebook-step-by-step.md) — handoff written by the orchestrator on 2026-11-04; step-by-step, with its checkboxes and records inside it. Records of step 0 (ACCEPTED 2026-11-04), step 1 (ACCEPTED 2026-11-05) and step 2 (ACCEPTED 2026-11-06) filled in by the orchestrator.
- [prompts index](../prompts/README.md) — handoffs 013 and 014 listed; further edits uncommitted in the working tree.
- [next_tasks.md](../next_tasks.md) — orchestrator edits: active slice updated and debt entries EDA-GSD and SANDBOX-SYNC added; the 014 → 015 supersession and the extent no longer blocking added 2026-11-05 (uncommitted). Bounding-box blocker marked resolved by the documenter.
- [EXP-001](../experiments/exp-001-data-feasibility.md) — orchestrator edits to Reproduction and Portability Constraints from handoff 013 (uncommitted); status, Configuration and Results updated by the documenter from the step 0, step 1 and step 2 records of handoff 015.
- [current_state.md](../current_state.md) — updated by the documenter for handoff 013, then for handoff 015 steps 0, 1 and 2.
- [notebooks/exp-001/README.md](../../notebooks/exp-001/README.md) — created by the developer in step 0 of handoff 015; states what the experiment measures, how to run it and which outputs are versioned. Finished in step 8.
- `docs/tfm/informe_01_muestra_datos_y_viabilidad.md` — thesis-side report for the supervisor, written 2026-11-05; untracked and pending the user's commit. `docs/tfm/**` is protected, so no agent reads or edits it.

## Date Started

2026-11-04

## Date Completed

<!-- YYYY-MM-DD -->
