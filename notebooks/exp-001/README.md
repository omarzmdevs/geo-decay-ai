# EXP-001 · What the data actually supports over one extent

The instrument of [EXP-001](../../docs/experiments/exp-001-data-feasibility.md).
Over **one** bounding box, it measures what the orthophoto, cadastre and
elevation services really supply, before any pipeline is built on top of them:

- which orthophoto years cover the extent, and the resolution each one really
  has (measured, not read from the catalogue);
- image quality per year, and whether near infrared is served;
- the cadastral footprints, their attributes, and whether any attribute could
  act as a weak label;
- the elevation rasters, their grids and value types;
- multi-epoch chip strips for example buildings and for manual samples, and
  the labelling table built from them;
- section 12, the findings, generated from what the run produced.

The experiment is **self-contained**. Everything it reads and writes lives in
this folder, so it can be moved whole. Nothing under `src/` imports it, it does
not import the package, and it sits outside the ADR-003 layer contracts. The
notebook is written in **Spanish**, by the user's decision; the module, this
README and every identifier are in English.

## Run it

```bash
uv sync --group eda
uv run --group eda python notebooks/exp-001/eda.py --selftest   # offline, no network
uv run --group eda jupyter lab notebooks/exp-001/01-eda-pnoa-catastro.ipynb
```

The `eda` dependency group is optional: a plain `uv sync` installs none of it.

**Restart the kernel and run the notebook in order, top to bottom.** Later
sections read what earlier ones left in memory (`MEASURED`, the footprints, the
years with imagery). Re-running only the first cells empties that state, and
section 12 then reports «no medido en esta ejecución» for everything it lost.

Two cells need a person, and neither blocks the cells after it:

- **Section 3** opens a map to draw the extent. The rectangle is written to
  `out/drawing.json` as soon as it is drawn, so a kernel restart does not lose
  it. Section 3.1 resolves it, or takes `EXTENT` and `EXTENT_CRS` from the
  parameter cell if they are filled in.
- **Section 10.2** opens a second, separate map for manual samples (see below).

The IGN, CNIG and Catastro domains are deliberately **not** in the agent sandbox
allowlist, so the measurement is run by a person on their own machine. An agent
can run the selftest and the notebook checker
(`python notebooks/exp-001/eda.py --check-notebook <path>`), both offline. Run
offline, the notebook reports `ABSENT:` with a reason in every section and still
reaches its last cell: that is a readable result, not a failure.

Figures are never stored inside the notebook: they are written to `out/figs/`
and shown from there, so a re-run does not rewrite megabytes of base64 into git.
**Do not open `out/manifest.csv` in JupyterLab while running**: a stale editor
tab writes its buffer back over the audit trail.

## Where outputs go

Everything lands under `out/`, beside the notebook. Response bodies are filed by
kind so the heavy ones can be ignored by folder.

| Path | What | In git |
|---|---|---|
| `out/manifest.csv` | one row per request: UTC time, URL, status, bytes, MD5, elapsed, error | yes |
| `out/drawing.json` | the extent rectangle as drawn, before snapping | yes |
| `out/extent.json` | the resolved, snapped extent with its report | yes |
| `out/ladder.csv` | one row per resolution rung, with each year's measured figure | yes |
| `out/strips.csv` | one row per building or manual sample and year asked: kept or dropped, and why | yes |
| `out/manual_samples.csv` | the manual samples, with the labelling table's columns | yes |
| `out/candidates.csv` | the labelling table | yes |
| `out/summary.md` | section 12's measured findings, with date, extent and commit | yes |
| `out/capabilities/`, `out/vectors/` | capabilities documents and feature replies the figures rest on | yes |
| `out/features/` | feature-info replies, if any were asked | yes |
| `out/epochs/`, `out/chips/` | rendered imagery and chips, re-fetchable | no |
| `out/elevation/` | elevation rasters, re-fetchable | no |
| `out/figs/` | figures the notebook shows from disk | no |

`manifest.csv` is the audit trail: **a figure with no manifest row behind it is
not a measurement.**

## Manual samples

The cadastre only holds what is registered, so section 10.2 lets a person mark
what it does not hold. Its map is separate from section 3's and never touches
the extent.

- The map opens with every sample already in `out/manual_samples.csv`.
- Draw, move or delete rectangles, then press **«Guardar muestras»**. Nothing is
  written before the button: it reconciles the whole map with the file, prints
  one line per action and redraws the map from what was saved. A new rectangle
  gets the next id (`M-0001`, `M-0002`, …); an edited one keeps its id.
- A sample may lie **inside or outside** the extent. Outside it is kept with a
  warning, because the cadastral overlap cannot be checked there. A longer side
  above `MANUAL_MAX_SIDE_M` is refused; one above a tile, or one overlapping a
  footprint, is kept with a warning. A sample whose row carries manual work in
  the labelling table cannot be deleted.
- The same rules apply again when sections 10.3 and 11 read the file, so a row
  written by hand cannot bypass them.

Section 10.3 gives each sample a strip and appends its rows to `strips.csv`, so
section 11 treats a sample like a building.

## The labelling table

`out/candidates.csv` has one row per cadastral footprint, then the manual
samples. It is written **comma-separated, UTF-8**. A copy saved by a spreadsheet
with `;` or a byte-order mark is read and rewritten in that format, and the
section says so. `label`, `evidence`, `notes` and `minutes_spent` are **carried
over by id** on every regeneration. The write is refused, and the file left
byte-identical, if an id holding manual work would disappear or if the file
cannot be read as the table.

## The provider is data

`PROVIDERS` in `eda.py` is the only place that names a host, a layer or a
vector attribute. Covering another country means adding an entry there, not
editing the notebook. Section 4 confirms or contradicts each claim of the entry
against the service's own capabilities document.

## Known limitations

- **Duplicate replies (EDA-DEDUP).** Each run stores a cadastral reply that
  differs from an earlier one only in the service timestamp and the order of
  features, and some manifest rows point to bodies later removed as duplicates.
  Section 12 reads such replies back from the newest row whose body still
  exists; the manifest's history is not rewritten.
- **The map's status label is saved empty.** The notebook's stored output of
  section 10.2 shows the label beside the button as empty; it is filled in a
  live session.
- **Section 12 needs a full run in order.** After re-running only some cells,
  the sections whose state was lost read «no medido en esta ejecución».

## How it was built

Section by section, under
[handoff 015](../../docs/prompts/015-eda-notebook-step-by-step.md): each section
was confirmed against the live services before the next one was written, and
the handoff's records are the history of the work.
