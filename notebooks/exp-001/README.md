# EXP-001 · What the data actually supports over one extent

The instrument of [EXP-001](../../docs/experiments/exp-001-data-feasibility.md):
it measures what the orthophoto service, the cadastre and the elevation
services really supply over **one** bounding box, before any pipeline is built
against them.

The experiment is **self-contained**. Everything it reads and writes lives in
this folder, so it can be moved whole, and nothing of it leaks into `data/`.
Nothing under `src/` imports it, it does not import the package, and it sits
outside the ADR-003 layer contracts.

The notebook is written in **Spanish**, by the user's decision; the module, this
README and every identifier stay in English.

## Run it

```bash
uv sync --group eda
uv run --group eda python notebooks/exp-001/eda.py --selftest   # offline, no network
uv run --group eda jupyter lab notebooks/exp-001/01-eda-pnoa-catastro.ipynb
```

The `eda` dependency group is optional: a plain `uv sync` installs none of it.

The IGN, CNIG and Catastro domains are deliberately **not** in the agent sandbox
allowlist, so the measurement is run by a person on their own machine. An agent
can run the selftest and the notebook checker
(`python notebooks/exp-001/eda.py --check-notebook <path>`), both offline. Run
inside the sandbox, the notebook reports absence everywhere and still reaches
its last cell: that is a readable result, not a failure.

A figure is never stored inside the notebook: it is written to `out/figs/` and
displayed from there, so a re-run does not rewrite a megabyte of base64 into
git. For the same reason, **do not open `out/manifest.csv` in JupyterLab while
running**: a stale editor tab will write its buffer back over the audit trail.

**The map needs a person between two cells.** *Run All* cannot work: section 3
opens a map, you draw a rectangle, and section 3.1 reads it back. The rectangle
is written to `out/drawing.json` the moment you draw it, so a kernel restart
does not cost you the extent.

## Where outputs go

Everything lands under `out/`, beside the notebook. Response bodies are filed by
kind so the heavy ones can be ignored by folder:

| Path | What | In git |
|---|---|---|
| `out/manifest.csv` | one row per request: UTC time, URL, status, bytes, MD5, elapsed, error | yes |
| `out/drawing.json` | the rectangle as drawn, before snapping | yes |
| `out/extent.json` | the resolved, snapped extent with its report | yes |
| `out/ladder.csv` | one row per resolution rung: year, pixels asked, m/px, status, bytes, MD5, residual, and the year's measured figure | yes |
| `out/candidates.csv`, `out/summary.*` | the labelling table and the run's findings | yes |
| `out/capabilities/`, `out/vectors/`, `out/features/` | the service documents the figures rest on | yes |
| `out/epochs/`, `out/chips/` | rendered imagery, re-fetchable | no |
| `out/figs/` | figures the notebook shows from disk instead of storing inline | no |

`manifest.csv` is the audit trail: **a figure with no manifest row behind it is
not a measurement.**

## The provider is data

`PROVIDERS` in `eda.py` is the only place that names a host, a layer or a vector
attribute. Covering another country means adding an entry there, not editing the
notebook. The entry's claims are unverified until section 4 of the notebook
confirms or contradicts each one against the service's own capabilities
document.

## How it is being built

Section by section, under
[handoff 015](../../docs/prompts/015-eda-notebook-step-by-step.md): each section
is confirmed against the live services before the next one is written, and the
checkboxes in that handoff are the state of the work. Sections 1 to 6.2
exist — the extent, the provider's claims, epoch availability, the measured
resolution and image quality; the rest arrive one step at a time.
