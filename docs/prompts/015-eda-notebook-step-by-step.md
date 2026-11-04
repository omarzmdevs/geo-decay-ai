# Handoff 015 · The EDA notebook, one section at a time

## Objective

Complete the Spanish EXP-001 notebook section by section inside a self-contained
experiment folder, each section confirmed against the live services by the user
before the next one is written.

## Role

developer

## Tier

`TIER_DEEP` — the same reason as handoff 014: the deliverable is the GIS
judgement about what each service actually supplies and which indicator that
makes computable, not the code around it.

## How this handoff runs — read this before anything else

**This handoff is not executed in one go, and never headless.** It is a list of
steps, each one its own exchange in an interactive developer session:

1. The developer writes the step's cells, **cleared**, and passes the offline
   gates.
2. The developer stops. No cell of a later step is written.
3. The user runs the notebook against the live services and pastes back what it
   printed.
4. The developer corrects what the real answers contradict.
5. The user closes the step. Its checkbox is ticked and its **Record** is filled
   in below.

Why it is built this way: handoff 014 delivered twelve sections in a single run,
every one of them verified offline, and the first contact with the live services
showed that the section that mattered most — the map that chooses the extent —
did not work at all, through three different causes in succession. A section
that has never printed a real service's answer is not finished; it is only
written. Offline verification proves a notebook does not crash. It cannot prove
it measures anything.

## Files to Read

- This handoff.
- `notebooks/exp-001/01-eda-pnoa-catastro.ipynb` — the instrument as it stands:
  sections 1, 2, 2.1, 3 and 3.1, with the map working.
- `notebooks/eda_helpers.py` — the accepted module of handoff 013, and the
  source `notebooks/exp-001/eda.py` is derived from in step 0.
- `docs/experiments/exp-001-data-feasibility.md` — only the part the current
  step measures.

Per step, nothing else. Do not read `src/**`. **Do not read
`notebooks/exp-001/_draft/`**: it is the previous case, kept only so a human can
look something up, and it is not an input to any step. If a step needs
something from it, the user names the file.

## Files to Create or Modify

- `notebooks/exp-001/01-eda-pnoa-catastro.ipynb` — grows one section per step.
- `notebooks/exp-001/eda.py` — created in step 0; afterwards only when a step
  cannot be written without a helper that is missing, and then named in that
  step's record.
- `notebooks/exp-001/README.md` — created in step 0, finished in step 8.

Everything the experiment reads or writes stays inside `notebooks/exp-001/`.

## Out of Scope

- `src/**`, `tests/**`, `scripts/**`, `pyproject.toml`, `uv.lock`.
- `notebooks/eda_helpers.py` and `notebooks/README.md` — read-only here. Whether
  they are deleted once the experiment is self-contained is a decision put to
  the user in step 8.
- `data/**`. The experiment no longer writes there; `data/interim/` keeps only
  its `.gitkeep`.
- Anything under `docs/`. Findings go in the notebook's own markdown; the
  orchestrator transcribes them into EXP-001.
- Reaching a data host from an agent session. The sandbox refuses the IGN, CNIG
  and Catastro domains by decision, and every offline criterion below is
  satisfied with every request failing.

## What does not carry over from the previous case

The user's decision of 2026-11-04, and it is deliberate: **no measured fact and
no provider correction is inherited.** The provider entry starts from the
committed values of handoff 013 and the first live run confirms or contradicts
them again. In particular `BU.Building`, `GetBuildingByBBOX`, `version="2"` and
`srsname="EPSG::{epsg}"` stay exactly as they are, even though a previous run
contradicted two of them.

Two mechanical consequences, both of them accepted:

- **The elevation service is gone.** It was a post-acceptance addition to the
  entry and went with the revert, so the entry describes no elevation endpoint.
  Section 9 therefore reports absence with "no endpoint in the provider entry",
  which is the correct output of step 5 rather than a failure, and **EXP-001
  question 2 has no instrument until the user decides to add one**. Tracked as
  EDA-ELEV.
- **Two things do carry over**, because the instrument needs them: the drawing
  round-trip (`save_drawing`, `load_drawing`, `forget_drawing`), which the
  notebook's working map calls in three places, and `fetch` catching a bare
  `OSError`, because criterion 5 of handoff 013 requires that a failed request
  always leaves a manifest row and the committed module does not honour it.

## Acceptance Tests

no — the notebook is the instrument, and the pair of checks below is what proves
each step: its offline run, and the user's live run.

## Criteria that apply to every step

1. **Cleared cells.** Every code cell delivered has `execution_count: null` and
   no stored outputs. The user's run is what carries outputs into the
   repository.
2. **Markdown before every code cell**, 4 to 8 lines of plain Spanish saying
   what the step does and why, ending with a line that begins `**Qué mirar:**`
   and names the thing in the output that decides the verdict. 120 to 180 words:
   handoff 014's prose ran to 793 words in one cell and was judged too heavy for
   a reader.
3. **The structure checker exits 0**:
   `uv run --group eda python notebooks/exp-001/eda.py --check-notebook
   notebooks/exp-001/01-eda-pnoa-catastro.ipynb`.
4. **Absence is a readable result.** Run offline, the notebook reaches its last
   cell, and every section with no data prints a line starting `ABSENT: ` with
   its own reason. No traceback, no cell left unexecuted, no `try` that hides
   the reason.
5. **No host, layer name, attribute name or coordinate** outside the parameter
   cell and the `PROVIDERS` entry of `eda.py`.
6. **Outputs only under `notebooks/exp-001/out/`**, resolved relative to the
   notebook's own directory so the folder can be moved whole. Images go to
   `out/epochs/` and `out/chips/`, which are git-ignored; `manifest.csv`,
   `extent.json`, `drawing.json`, `candidates.csv`, `summary.*` and
   `out/capabilities/*.xml` are versioned.
7. **The full gate passes**: `uv run pre-commit run --all-files`.
8. The step's own criterion, below.

## Steps

- [ ] **0 · The self-contained folder**
- [ ] **1 · Section 4 · Provider capabilities**
- [ ] **2 · Sections 5 and 6 · Epoch availability and image quality**
- [ ] **3 · Section 7 · Spectral check**
- [ ] **4 · Section 8 · Cadastral footprints**
- [ ] **5 · Section 9 · Elevation availability**
- [ ] **6 · Sections 10 and 11 · Example buildings and the labelling table**
- [ ] **7 · Section 12 · Findings**
- [ ] **8 · Close**

---

### Step 0 · The self-contained folder

**Objective.** The experiment runs from its own folder, with no reference to
`notebooks/eda_helpers.py` and nothing written under `data/`.

The folder and the notebook's move into it were done by the user on 2026-11-04.
What is missing is the module, the README and the notebook's parameter cell.

**Touches.** `notebooks/exp-001/eda.py` (create), `notebooks/exp-001/README.md`
(create), the notebook's parameter and utilities cells.

`eda.py` is the accepted module of handoff 013 with exactly these differences,
and no others: output routing into `out/` and its three subfolders so the ignore
rules hold; the drawing round-trip; `fetch` catching `OSError` as well as
`requests.RequestException`; and `--check-translation` dropped, since there is
no second notebook to keep in step. The `PROVIDERS` entry is copied unchanged.

**Criterion.** `--selftest` exits 0 and covers the drawing round-trip and a bare
`OSError` reaching the manifest. The notebook runs offline to its last cell,
imports `eda`, writes nothing outside `out/`, and resolves the extent from
`out/drawing.json` when one is there. `git status --short` shows nothing under
`data/`.

**Settles.** Nothing about the services. This step is the move, and the reason
it is a step at all is that nothing below can be verified until the instrument
is self-contained.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 1 · Section 4 · Provider capabilities

**Objective.** Confirm or contradict the provider entry against the services'
own capabilities documents, before any figure is measured through it.

**Criterion.** One row per claim the entry makes — every advertised CRS, every
layer name, the epoch layer pattern, the stored query, each vector attribute —
with a verdict of `ok`, `unverified` or a named `MISMATCH` carrying the nearest
names the service does advertise. The CRS list the service publishes, and
whether the chosen extent's CRS is among them. A wrong value is **reported, not
repaired in this step**: the correction is a separate edit the user approves.

**Settles.** The layer names, the CRS list, the epoch pattern and the stored
query. It is also the cheapest step to run, so it is the one that tells us
whether the entry is worth anything before 22 epochs are probed through it.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 2 · Sections 5 and 6 · Epoch availability and image quality

**Objective.** Establish which years cover the extent and whether their imagery
is readable at all.

**Criterion.** Section 5: one row per year in the parameterised range with
status, bytes, MD5, blank verdict and declared ground sample distance, each GSD
carrying the source it was read from — a resolution nobody declared is never
reported as measured. Section 6: per-epoch statistics and a thumbnail grid,
flagging blank, saturated and low-contrast epochs. Both degrade to `ABSENT`
with a reason per epoch.

**Settles.** EXP-001 question 1 — the years and the real resolution. It is also
the heaviest step in bytes, which is why it comes after step 1.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 3 · Section 7 · Spectral check

**Objective.** Determine whether a near-infrared band or an infrared composite
layer is served, and state the consequence when it is not.

**Criterion.** The section names what it looked for, what it found and what
follows: without a NIR band NDVI is off the table and every vegetation variable
has to come from RGB surrogates, which confuse plants with green roofing and
shaded ground. That consequence is written in the notebook, not left implied.

**Settles.** Part of EXP-001 question 3 — which indicators are computable.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 4 · Section 8 · Cadastral footprints

**Objective.** Measure what the cadastre supplies over the extent, and whether
its attributes can act as weak labels.

**Criterion.** Format, CRS, feature count, the full attribute inventory, value
counts for the condition and age attributes, and the footprints drawn over the
latest available orthophoto. Every attribute the entry claims is reported as
present or absent by its real name.

**Settles.** The WFS parameters the previous case left contradicted — the stored
query, the version string and the `srsname` form — and the basis of EXP-001
question 4.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 5 · Section 9 · Elevation availability

**Objective.** Report, per elevation product, whether a service covers the
extent and in what form.

**Criterion.** Elevation services are discovered generically, by token in the
entry's logical keys, so the section starts probing with no change to the
notebook the moment the entry gains one. With the entry as it stands, every row
reads `ABSENT: … no endpoint in the provider entry, so nothing was probed`, and
**that is this step passing**. The national download portal is not made an
endpoint: it has no OGC interface, and an unknown layer name is sent to the
epoch service, so a portal answering 200 with HTML would be recorded as a point
cloud that is available — the worst available outcome on this question.

**Settles.** Nothing, by construction, until the user decides to add an
endpoint. The step exists so that the gap is visible in the notebook instead of
being silently skipped. EDA-ELEV.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 6 · Sections 10 and 11 · Example buildings and the labelling table

**Objective.** Produce the material the manual pass of EXP-001 step 6 needs.

**Criterion.** For N buildings, one multi-epoch chip strip each, oldest to
newest, with the year on every chip. `candidates.csv` with one row per footprint
and empty `label`, `evidence`, `notes` and `minutes_spent` columns, written with
its header even when there are no rows.

**Settles.** The real manual cost per building, which is what makes EXP-001
question 4 answerable rather than estimated.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 7 · Section 12 · Findings

**Objective.** Say what this instrument measured, what it could not, and which
abandonment variables the measurement supports.

**Criterion.** Three markdown subsections — what can be extracted, problems
found, candidate variables for abandonment — plus a cell writing `summary.md`.
What the run measured is separated from what is inferred, under headings that
say so, and each of EXP-001's four questions is marked answered or not answered
with the reason beside it. Only figures the previous steps actually produced
appear here.

**Settles.** The sprint's deliverable: the measurement exists and is readable.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

### Step 8 · Close

**Objective.** Leave the folder in a state a third party can run.

**Criterion.** `notebooks/exp-001/README.md` states what the experiment
measures, how to run it, where every output goes and which outputs are
versioned. A prose pass brings every markdown cell inside the 120-to-180-word
budget. The full gate passes and `git status --short` shows only files inside
`notebooks/exp-001/`.

Two decisions are **put to the user**, not taken here: whether
`notebooks/eda_helpers.py` and `notebooks/README.md` are deleted now that the
experiment is self-contained, and whether `notebooks/exp-001/_draft/` stays on
disk.

**Record** — filled in when the step closes.

- Date:
- What the live run printed:
- Corrections applied:
- Verdict:

---

## Verification Command

Run at the end of **every** step, before handing it back:

```bash
uv sync --group eda
uv run --group eda python notebooks/exp-001/eda.py --selftest
uv run --group eda python notebooks/exp-001/eda.py --check-notebook \
  notebooks/exp-001/01-eda-pnoa-catastro.ipynb
uv run pre-commit run --all-files
git status --short
```

Plus an offline execution of the notebook, which is what proves criterion 4.
`jupyter nbconvert --execute` **cannot run in the agent sandbox**: a kernel needs
a local socket and local port binding is off, which was reproduced twice during
handoff 014. The documented substitute is executing the cell sources unchanged
in-process through `IPython.core.interactiveshell.InteractiveShell`, with
`enable_gui` patched to a no-op so `%matplotlib inline` does not raise outside a
real kernel. Equivalent in substance, not identical, and the difference is
recorded in the step's record. The literal command runs on the user's machine,
which is where the measurement happens anyway.

## Launch Command

**None, by design.** This handoff is not launched headless and not run from a
single prompt. The user opens an interactive developer session and names the
step:

```
ROL: Desarrollador. Ejecuta el paso N de
docs/prompts/015-eda-notebook-step-by-step.md
```

The session ends when that step's offline gates pass. The user's live run, and
the step's record, close it.

## Restore Point

The commit that carries this handoff, whose parent is
`652cf5698aac8b0b26eeff24926445b51661b210`. The working tree it starts from
holds the records of handoffs 013 and 014, the ignore rules of the
self-contained folder, and the notebook with its map working. Whoever opens step
0 records the exact hash in that step's record.
