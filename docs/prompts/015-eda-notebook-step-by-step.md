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

- [x] **0 · The self-contained folder** — ACCEPTED 2026-11-04
- [x] **1 · Section 4 · Provider capabilities** — ACCEPTED 2026-11-05
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

- Date: 2026-11-04
- What the live run printed: nothing — step 0 touches no service. Verified
  offline instead: `eda.py --selftest` passes 25 checks, `--check-notebook`
  exits 0, `pre-commit run --all-files` passes all six hooks, and the notebook
  reaches its last cell with `ABSENT:` plus its diagnostic panel. It imports
  `eda`, writes nothing outside `out/` except `__pycache__`, resolves the extent
  from `out/drawing.json` after a simulated kernel restart and regenerates the
  same `extent.json`, and the map's bin button deletes the drawing while a
  registered extent survives. `jupyter nbconvert --execute` could not run (no
  local socket in the sandbox); the documented in-process substitute was used.
  Restore point: `5bb3241`. `eda.py` is derived from the accepted module of
  handoff 013 with exactly the four differences this step allows, and the
  `PROVIDERS` entry was copied unchanged, so `BU.Building`,
  `GetBuildingByBBOX`, `version="2"` and `srsname="EPSG::{epsg}"` all stand
  unverified, as this handoff requires. `notebooks/exp-001/` holds three
  versioned files after this step — `eda.py`, `README.md` and
  `01-eda-pnoa-catastro.ipynb` — with `_draft/`, `out/epochs/`, `out/chips/`
  and `__pycache__/` confirmed ignored.
- Corrections applied: the parameter panel lost a trailing `/`, which the
  notebook checker reads as an absolute path when it begins an f-string literal
  part. One thing outside the step's scope was reported to the user rather than
  changed: the user's own drawn rectangle sits in
  `notebooks/exp-001/_draft/drawing.json` and was not copied into `out/`,
  because this handoff forbids taking anything out of `_draft/` unless the user
  names it.
- Verdict: ACCEPTED

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

**Record**

- Date: live run 2026-11-04 by the user, from restore point `25b58f0`; the work
  landed in `339ea81`; verified by the orchestrator 2026-11-05.
- What the live run printed: 4 of 4 services answered, 26 CRS in the union, 56
  advertised layers, 5 stored queries and **3 contradictions** over 14 claim
  rows. Re-derived independently on 2026-11-05 from the five capability
  documents that run committed (`out/capabilities/*.xml`, 27902 + 113091 +
  28799 + 16182 + 1770 bytes; five manifest rows, all status 200, each MD5
  matching its filename): the same 26 CRS, 56 layers and 5 stored queries, all
  four claimed CRS advertised, `OI.OrthoimageCoverage` advertised, the extent's
  own `EPSG:25830` advertised, and `PNOA2004`–`PNOA2024` served — 21 year
  layers, not 22. The three contradictions:
  1. **`layers["buildings"] = ("cadastre_wms", "BU.Building")`** — the cadastral
     WMS advertises 13 layers and none of them is `BU.Building`; the footprint
     layer it does serve is `CONSTRU`. The INSPIRE name exists, but on the WFS
     (`bu:Building`), not on the WMS. Reported, not repaired: the entry
     correction waits for the user.
  2. **The epoch pattern over 22 years** — `PNOA2025` is not advertised. That
     was the notebook's `YEAR_LAST`, a parameter of this handoff's own making
     and not a claim of the provider entry, so it was corrected and the verdict
     now reports the real served range and the gap instead of reading a missing
     year as a contradiction.
  3. **`STOREDQUERIE_ID = "GetBuildingByBBOX"`** — not among the five the WFS
     advertises (`GetBuildingByParcel`, `GetFeatureById`,
     `GetBuildingPartByParcel`, `GetOtherBuildingByParcel`,
     `GetAllConstructionByParcel`). None of them takes a bounding box, so step 4
     has to query `TYPENAMES` + `BBOX` directly. Reported, not repaired.

  The five vector attributes stayed `unverified` by design: they arrive with the
  features, in step 4.
- Three findings the step was not looking for, all read from the same five
  documents:
  - The historical service advertises **37 layers, not 21**: besides
    `PNOA2004`–`PNOA2024` it serves `AMS_1956-1957`,
    `Interministerial_1973-1986`, `Nacional_1981-1986`, `OLISTAT`, `SIGPAC`,
    six regional `pnoa10_*`, two `OrtoExpeditaLIDAR*` and an `infoVuelos`
    coverage layer. The depth available over the extent is ~70 years, not 20,
    which changes what a change-detection design can look at.
  - **No layer declares a resolution** anywhere machine-readable — the titles
    are "PNOA 2024" and nothing more — so the entry's `default_gsd_m = 0.25` is
    an assumption, not a measurement. Step 2 must measure it against ground
    metres rather than report it.
  - **No NIR band and no infrared composite** among the 56 layers. That is
    step 3's answer arriving early; section 7 still has to state it and its
    consequence in the notebook.
- Corrections applied: `YEAR_LAST` 2025 → 2024, and the epoch verdict reworked
  as described above. Nothing in the `PROVIDERS` entry was touched, as this step
  requires.
- Entry correction applied after acceptance, on the user's approval of
  2026-11-05: `layers["buildings"]` now reads `("cadastre_wms", "CONSTRU")`, the
  layer the cadastral WMS actually advertises. One line and a comment in
  `notebooks/exp-001/eda.py`; the WFS path is untouched, because `wfs_buildings`
  builds its request from `wfs_params` and never from `layers`, and the notebook
  never names the layer — it reaches a request only through `_resolve_layer`.
  Re-proved offline against the committed cadastral document: `CONSTRU` is among
  its 13 layers, `BU.Building` is not. Contradiction 1 is closed;
  `GetBuildingByBBOX` stays open for step 4.
- Gate, re-run on 2026-11-05: `pre-commit run --all-files` passes all six hooks,
  `eda.py --selftest` passes 31 checks, `--check-notebook` exits 0, and the
  notebook is 11 cells, `MMCMCMCMCMC`, with every code cell cleared.
- Verdict: ACCEPTED

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

**Amendment 2026-11-06 — the native resolution is measured, not only read.**
As written above, this step's criterion asks only for the *declared* ground
sample distance, while its "Settles" promises "the real resolution", and the
EXP-001 record says step 2 must measure it. No later step closes that gap:
section 7 is spectral, sections 10 and 11 are chips and the labelling table,
section 12 reports what earlier steps produced. The promise was therefore
implemented nowhere. Section 5 is accepted and is not reopened; the measurement
is added to **section 6**, which is not written yet, as a further criterion of
this step. Found while supervising step 2, on the user's prompting.

Section 6 must also establish, **per year and never globally**, the ground
sample distance each epoch really carries:

- **Over one tile-sized ground window**, not the extent: `TILE_PX` × the
  entry's `default_gsd_m`, centred in the extent. It is small in bytes and it
  is the window the pipeline will actually use.
- **A ladder of request sizes over that same window** — 128, 256, 512, 1024,
  2048 px — each one a manifest row. The service declares no `MaxWidth` or
  `MaxHeight`, so the real cap is discovered by asking: a refusal is a recorded
  finding, not a failure, and the ladder stops there.
- **Ask for PNG.** The service offers it, and a lossless reply removes the
  compression this measurement would otherwise have to fight. Any JPEG already
  baked into the mosaic upstream remains, and raises the high-frequency floor,
  so the statistic must tolerate a floor rather than assume silence above the
  cutoff.
- **The statistic is the developer's choice, but it must be named in the
  notebook and proved in `--selftest` against ground truth built offline**: an
  image upsampled from a known resolution must have that resolution recovered.
  A measurement whose estimator is not falsifiable offline does not count.
- **The verdict per year** is the finest ground sample distance at which detail
  still grows; everything finer is the service upsampling. A curve that never
  flattens means the ladder did not reach far enough, and is reported as that —
  never by taking the last rung as the answer.
- **Only for the years section 5 marked `present`**, so the byte cost stays
  proportionate.
- **The output states how many pixels a building occupies** at the measured
  resolution, with the building size a declared parameter and labelled an
  assumption: the real distribution of footprints arrives in section 8. That
  number, not the metres per pixel, is what decides feasibility.
- **A per-year difference is a finding**, not an inconsistency to smooth over:
  the service declares 50, 25 and 15 cm depending on year and region.

Until this is measured, `default_gsd_m = 0.25` stays an assumption everywhere
it is used, including the tile arithmetic of the extent report.

**Settles.** EXP-001 question 1 — the years and the real resolution, the second
of those only with the amendment above. It is also the heaviest step in bytes,
which is why it comes after step 1.

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
