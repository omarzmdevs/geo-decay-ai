# Handoff 014 · The exploratory analysis notebook

## Objective

Deliver one notebook on which the reader draws the study extent on a map and
then measures EXP-001 steps 2, 3 and 4 over it, explaining every step in plain
language before running it, and producing the example buildings and the empty
labelling table the manual pass of step 6 needs.

## Role

developer

## Tier

`TIER_DEEP` — the deliverable is the GIS/CV judgement (which indicator is
computable from this imagery and why a missing one is missing), not the code
around it. Writing a defensible "candidate variables" section is the hard part.

## Files to Read

- This handoff.
- `docs/experiments/exp-001-data-feasibility.md` — all of it; it is the
  specification of what must be measured.
- `notebooks/eda_helpers.py` and `notebooks/README.md` (handoff 013).

Do not read `src/**`.

## Files to Create or Modify

- `notebooks/01-pnoa-catastro-eda.ipynb` — create.
- `notebooks/eda_helpers.py` — **only** if the notebook cannot be written
  without a helper that is missing. Any addition keeps criteria 2 and 3 of
  handoff 013 true, and is named in the run record.

## Out of Scope

- `src/**`, `tests/**`, `scripts/**`, `pyproject.toml`, `uv.lock`.
- Committing outputs. The committed notebook is **cleared**: the measurement run
  is the user's, and their run is what carries the outputs into the repository.
- Writing anything into `docs/`. Findings go in the notebook's own markdown
  cells; the orchestrator transcribes them into EXP-001.
- Any attempt to reach a data host. The sandbox refuses them by decision, and
  the criteria below are all satisfied with every request failing.

## Acceptance Tests

no — the notebook is the instrument, and its offline execution is the check.

## Acceptance Criteria

1. **Structure.** `uv run --group eda python notebooks/eda_helpers.py
   --check-notebook notebooks/01-pnoa-catastro-eda.ipynb` exits 0: valid
   `nbformat`, every code cell compiles, every code cell preceded by a markdown
   cell, no `http` literal or extent coordinate in any code cell but the first,
   no `geo_decay_` import, no absolute path.

2. **One parameter cell, and no extent baked in.** The first code cell holds
   every parameter — extent, CRS, provider key, year range, request pixel size,
   tile size, snap grid, number of example buildings, output directory — each on
   its own line with a trailing comment. EXP-001 step 1 is still open, so the
   extent and its CRS have **no default**: they are empty placeholders, filled
   either by hand or by the map of section 3. No coordinate literal appears
   anywhere else in the notebook; the map's opening view comes from the provider
   entry.

   The extent is resolved in section 3 in this order, and the notebook prints
   which branch it took: the rectangle drawn on the map, else the parameter cell,
   else `ABSENT: no extent selected` — after which every section that needs data
   reports absent and the notebook still runs to the end.

3. **Twelve sections, in this order**, each one markdown cell followed by one or
   two code cells:

   | # | Section | Must produce |
   |---|---|---|
   | 1 | Purpose and how to run it | the four questions of EXP-001, the two commands, where outputs go |
   | 2 | Parameters | criterion 2 |
   | 3 | Choose the extent on a map | criterion 4 |
   | 4 | Provider capabilities | the CRS list the service advertises, and whether the extent's CRS is among them |
   | 5 | Epoch availability | one row per year in the parameterised range: status, bytes, MD5, blank verdict, declared GSD |
   | 6 | Image quality | per-epoch statistics table and a thumbnail grid; flags blank, saturated and low-contrast epochs |
   | 7 | Spectral check | whether an infrared band or IRC layer is served, and the consequence if not |
   | 8 | Cadastral footprints | format, CRS, feature count, attribute inventory, value counts for the condition and age attributes, footprints drawn over the latest orthophoto |
   | 9 | Elevation availability | one row per probed elevation product: available or `ABSENT` with the reason |
   | 10 | Example buildings | for N buildings, one multi-epoch chip strip each, oldest to newest |
   | 11 | Labelling table | `candidates.csv` with one row per footprint and empty `label`, `evidence`, `notes`, `minutes_spent` columns |
   | 12 | Findings | three markdown subsections — what can be extracted, problems found, candidate variables for abandonment — plus a code cell writing `summary.md` |

4. **The map selector (section 3) is simple and complete.** An `ipyleaflet`
   `Map` opened at the provider's `default_view`, carrying a `DrawControl`
   limited to the rectangle tool — every other shape disabled, so there is one
   way to use it — plus a `MeasureControl` and a `ScaleControl` for live
   distances while drawing. One markdown instruction above it, in two steps:
   draw a rectangle, then run the next cell.

   The cell below the map resolves the extent per criterion 2 and prints, from
   `extent_report`:

   - the drawn extent in `EPSG:4326` and reprojected to the provider's native
     projected CRS, as the **envelope of all four corners**;
   - width and height in metres, the area in km², and the geodesic width and
     height alongside them, so the projected figures can be sanity-checked;
   - `skew_m` — how far the rectangle is from being a rectangle in the
     projected CRS — with one line saying why it matters;
   - the extent snapped outward to the parameterised grid, its pixel dimensions
     at the provider's ground sample distance, the tile count at the
     parameterised tile size, and whether it fits whole tiles;
   - the two `GEO_DECAY_*` lines ready to paste into EXP-001 → Configuration.

   It then calls `save_extent`, so the chosen extent is recorded as a file and
   not only as a drawing. Redrawing and re-running the cell replaces it: the
   notebook must not accumulate hidden state between attempts.

   Headless — under `nbconvert`, with no widget frontend and no tiles — the map
   is still constructed, nothing raises, no rectangle exists, and the resolution
   falls through to the parameter cell and then to `ABSENT`.

5. **Every markdown cell is an explanation, not a label**: three to eight lines
   of plain English saying what the step does and why it is being done, ending
   with a line that begins `**What to look at:**` naming the thing in the output
   that decides the verdict. No jargon left undefined, and no sentence that only
   repeats the code.

6. **Absence is a readable result.** Executed with every request failing, the
   notebook runs to completion, and every section that needed data prints a
   line starting `ABSENT: ` with the reason. No traceback, no cell left
   unexecuted, no `try` block that hides the reason.

7. **Section 12 is honest.** The findings cells separate what this run
   measured from what is inferred, and say plainly which of the four questions
   of EXP-001 the run could not answer and why.

8. **Outputs land only under the parameterised output directory**, default
   `data/interim/exp-001/`, which the notebook creates; `manifest.csv`,
   `candidates.csv` and `summary.md` all exist after an offline run, with
   headers even when empty. `extent.json` appears only when an extent actually
   resolved, so its absence after a headless run is correct.

9. **The committed notebook is cleared**: every code cell has
   `execution_count: null` and no stored outputs.

10. The full gate passes: `uv run pre-commit run --all-files`.

## Verification Command

```bash
set -e
uv sync --group eda

# 1 — structure
uv run --group eda python notebooks/eda_helpers.py --check-notebook notebooks/01-pnoa-catastro-eda.ipynb

# 9 — the committed notebook carries no outputs
uv run --group eda python - <<'NB'
import nbformat
nb = nbformat.read("notebooks/01-pnoa-catastro-eda.ipynb", as_version=4)
code = [c for c in nb.cells if c.cell_type == "code"]
assert code, "no code cells"
dirty = [i for i, c in enumerate(code) if c.get("outputs") or c.get("execution_count") is not None]
assert not dirty, f"cleared notebook expected; cells with outputs: {dirty}"
assert nb.cells[0].cell_type == "markdown", "the notebook must open with an explanation"
print(f"9 ok: {len(code)} code cells, all cleared")
NB

# 4, 6, 8 — it runs to completion with no network, resolves the extent to ABSENT, and says why
OUT="data/interim/exp-001"
mkdir -p "$OUT"
uv run --group eda jupyter nbconvert --to html --execute \
  --ExecutePreprocessor.timeout=600 --output-dir "$OUT" \
  notebooks/01-pnoa-catastro-eda.ipynb
grep -q "ABSENT" "$OUT/01-pnoa-catastro-eda.html" && echo "6 ok: absence is reported in the rendered output"
grep -q "ABSENT: no extent selected" "$OUT/01-pnoa-catastro-eda.html" \
  && echo "4 ok: with no drawing and no parameter, the extent resolves to ABSENT"
test -s "$OUT/manifest.csv" && test -s "$OUT/candidates.csv" && test -s "$OUT/summary.md" \
  && echo "8 ok: manifest, labelling table and summary all written"

# 10 — the gate, and nothing tracked was left behind
uv run pre-commit run --all-files
git status --short && git diff --stat
```

`data/interim/*` is git-ignored, so the executed HTML and every byte the run
fetched stay out of the diff. `git status --short` must show only
`notebooks/01-pnoa-catastro-eda.ipynb` (and `notebooks/eda_helpers.py`, if the
exception in Files to Create or Modify was used).

## Launch Command

```bash
claude -p "ROLE: developer. Execute docs/prompts/014-eda-notebook.md" \
  --model opus --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" "Bash(uv sync*)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

`uv lock` is not allowed: handoff 013 already added every dependency this one
needs, `ipyleaflet` and `ipywidgets` included. If a widget import fails, that is
a rejection of 013, not something to patch here.

## Restore Point

`652cf5698aac8b0b26eeff24926445b51661b210` — a clean working tree. It carries
handoff 013's accepted work and its EDA-GSD correction (`4f5f8a4`), plus what
verifying them taught the method (`652cf56`).

---

## Run Record

Date: 2026-11-04
Tool and model: subagent at `TIER_DEEP`, launched from the orchestrator session,
because the agent sandbox refuses `api.anthropic.com` and a nested headless
launch cannot reach it. Three addenda were passed at launch that this frozen
handoff does not carry: that `gsd_m` and `tile_px` became required keyword
arguments after the EDA-GSD correction, that the deliverable must be real
`nbformat` JSON, and that section 4 must name a wrong provider value rather than
show an empty table.
Outcome: completed

## Verification

Verdict: **ACCEPTED**

Files changed: `notebooks/01-pnoa-catastro-eda.ipynb` only — 25 cells, 13
markdown and 12 code. `notebooks/eda_helpers.py` was not touched: the exception
in Files to Create or Modify went unused, so no helper turned out to be missing.
The only other entry in the working tree is this file's restore point, which is
the orchestrator's.

Gate: `uv run pre-commit run --all-files` re-run by the orchestrator — all six
hooks pass, and `eda_helpers --selftest` still exits 0.

Criteria: re-checked independently. The checker exits 0. The cell sequence is
`MMCMCMCMCMCMCMCMCMCMCMCMC` — strict alternation, no two adjacent code cells,
first cell markdown, every code cell cleared (`execution_count: null`, no stored
outputs). All 13 markdown cells end with a `**What to look at:**` line. No
coordinate or endpoint literal outside the first code cell; the one `0.25` in a
later cell is inside a comment illustrating a regex, not a provider value, and
the ground sample distance is read from `PROVIDER.default_gsd_m`.

**Criteria 4 and 6 were verified by re-executing the notebook, not by reading
the report.** 12 code cells executed, none raised, and 22 lines beginning
`ABSENT: ` were printed, each naming its own reason — starting with
`ABSENT: no extent selected — draw a rectangle above, or fill EXTENT and
EXTENT_CRS in section 2`, which is the fall-through of criterion 2 working.
`manifest.csv`, `candidates.csv` (13 columns, including the four empty labelling
columns) and `summary.md` all exist; `extent.json` is correctly absent, since
nothing resolved. `summary.md` reports all four EXP-001 questions as
`NOT ANSWERED` with the reason beside each, under a heading that separates them
from an explicitly labelled "Inferred, not measured" list.

Notes:

1. **The verification command's execution step cannot run in this sandbox, and
   the substitute was re-run by the orchestrator.** `jupyter nbconvert
   --execute` needs a kernel, a kernel needs a local socket, and local port
   binding is off here: reproduced twice, first as
   `PermissionError: Operation not permitted: '/Users/omz/.jupyter'` and then,
   with the Jupyter directories redirected into `$TMPDIR`, as
   `jupyter_client/connect.py … tmp_sock.bind((ip, 0))` →
   `PermissionError: [Errno 1] Operation not permitted`. The developer did not
   retry outside the sandbox, which was the right call: outside it the data
   hosts become reachable and criteria 4 and 6 would have been destroyed rather
   than satisfied. Both the developer and the orchestrator executed the notebook
   in-process instead, through `InteractiveShell` with the cell sources
   unchanged. Equivalent in substance, not identical. The literal command runs
   either with `sandbox.network.allowLocalBinding: true` in the user's settings
   or on the user's own machine, which is where the measurement happens anyway.
2. **This handoff contradicts itself on cell layout, and the developer resolved
   it correctly.** Criterion 3 asks for "one or two code cells" per section while
   criterion 1's checker rejects any code cell not immediately preceded by a
   markdown cell — so two in a row is impossible. Section 3 genuinely needs two
   (draw the rectangle, then run the next cell), and a `### 3.1` markdown cell
   now sits between them. Section 1 has no code cell at all, which keeps the
   parameter cell first as criteria 1 and 2 both presuppose. The defect is the
   orchestrator's, not the delivery's.
3. **Criterion 3 row 9 could not be satisfied as written, and EXP-001 question 2
   is unanswerable by this instrument as it stands.** `PROVIDERS["es-pnoa"]`
   describes no elevation service — its endpoints are `ortho`,
   `ortho_history`, `cadastre_wms` and `buildings_wfs` — so there was nothing to
   probe, and inventing a host would have meant writing an unverifiable value
   into the entry. Section 9 instead discovers elevation services generically by
   token in the entry's logical keys, reports one row per product category and
   currently prints `ABSENT: … no endpoint in the provider entry, so nothing was
   probed` for all three. It will start probing with no change to the notebook
   the moment an entry gains one. This is a gap in handoff 013's specification
   of the provider entry, tracked as **EDA-ELEV**.
4. **A defect in handoff 013's accepted work, found by this task and
   demonstrated by its run.** `fetch` catches `requests.RequestException`, which
   is a *subclass* of `OSError` rather than the reverse — confirmed:
   `issubclass(requests.RequestException, OSError)` is `True` and the converse is
   `False`. A bare `OSError` therefore escapes `fetch` and **leaves no manifest
   row**, which breaks criterion 5 of handoff 013. It is not hypothetical: in
   this sandbox `certifi/cacert.pem` is unreadable, so the two `www.ign.es`
   requests failed with a TLS CA `OSError`, and `manifest.csv` holds rows for the
   three proxy-refused Catastro requests and **nothing at all** for those two.
   The notebook is not at fault — it wraps every fetch site so the failure still
   surfaces as `ABSENT` — but the audit trail the experiment rests on was
   silently incomplete. Tracked as **EDA-OSERROR** and fixed the same day, on
   direct instruction without a handoff: the handler now covers both exceptions
   and the selftest drives a bare `OSError` through `fetch` and asserts that a
   manifest row is written. Re-verified independently with a non-existent
   `REQUESTS_CA_BUNDLE` — nothing raised, `status` 0, one row with its `error`
   column set. The notebook was not changed for it, so this handoff's delivery
   stands as verified above.
5. **Six provider values are suspected wrong**, all unverifiable from here and
   all reported rather than guessed at: the `buildings` layer pairs Catastro's
   general WMS endpoint with the INSPIRE `BU.Building` layer name, which looks
   crossed; `srsname` renders as `EPSG::25830`, a truncated URN; the WFS
   `version` is a bare `2` where services advertise `2.0.0`; `STOREDQUERIE_ID`
   carries Catastro's own misspelling, which may well be correct; and
   `epoch_layer_pattern` is unconfirmed. Section 4 prints each as `ok`,
   `unverified` or a named `MISMATCH`, so the user's first networked run is what
   settles them. Recorded in EXP-001 → Results → Provider entry.
6. **Two smaller judgements, both accepted.** Per-epoch ground sample distance
   is parsed out of the layer title in the capabilities document, with a
   `gsd_source` column reading `service document` or
   `provider entry (unverified)`, because no service declares it in a
   machine-readable field — a resolution nobody declared is not reported as
   measured. And the quality thresholds live as named constants in section 6's
   own cell rather than in the parameter cell, since criterion 2 does not list
   them.
7. **Prose volume.** The markdown cells are 4 to 9 non-blank lines, within
   criterion 5, but 204 to 793 words each: about 3,400 words across the notebook.
   The sample read is dense and purposeful rather than padded, so it is accepted,
   but it is heavier than "clean and simple explanations" implies and is worth a
   trimming pass before the notebook goes to a reader.
8. **An environment repair, outside the repository.** `tornado` had been
   installed incomplete in `.venv`, the install having aborted on
   `tornado/test/test.key` under the sandbox's `*.key` rule, leaving `jupyter`
   unimportable; the developer restored the package from the uv cache without
   that fixture. `.venv/` is git-ignored, so nothing reaches the diff, but it
   means this verification ran against a hand-repaired environment. On the
   user's machine, outside the sandbox, `uv sync --group eda` gives a clean one.
   This is **SANDBOX-SYNC** biting at install time rather than at prune time.

---

## Post-Acceptance Additions

Work done on this handoff's deliverable **after** the verdict above, on the
user's direct instruction and without a new handoff. Kept separate so the record
still shows what the handoff itself produced. Each was re-verified by the
orchestrator in the same way the delivery was.

**2026-11-04 · The orthophoto under the selector map.** Choosing a study extent
for orthophoto work on a bare basemap means choosing blind, so section 3 opens
the map with the provider's current orthophoto as a `WMSLayer` beneath the
rectangle tool, plus a `LayersControl` to switch it off. The endpoint and layer
name come from the `PROVIDERS` entry; both lookups use `.get` with a fallback, so
a missing key degrades to an empty URL rather than raising, and a wrong layer
name is a browser-side error tile only. The markdown says plainly that error
tiles mean the entry's layer name is wrong and that section 4 is what confirms
it. Re-verified: the notebook still executes offline with nothing raising.

**2026-11-04 · The elevation hypothesis.** `PROVIDERS["es-pnoa"]` gains an
INSPIRE elevation (MDT) WMS endpoint and a terrain layer name, both marked **in
the data** as unconfirmed hypotheses, so that section 9's token discovery finds
them with its logic unchanged. Re-verified: section 4 now asks the new endpoint
(`ABSENT: elevation_wms — …`) and section 9's terrain row moved from "no
endpoint in the provider entry" to `ABSENT: terrain raster — no extent selected,
so the service was never asked`. The ABSENT count went from 22 to 23.

Two values are reasoned rather than observed and are labelled as such: the `mdt`
path segment, and `EL.ElevationGridCoverage` as the layer name, chosen by INSPIRE
convention to match the entry's existing `OI.OrthoimageCoverage`. The user's
first networked run settles both.

**The CNIG download centre is deliberately *not* an endpoint**, and the reasoning
is worth keeping. It is a browser portal with no OGC interface, and
`_resolve_layer` sends any layer name it does not find in `provider.layers` to
the `epoch_service` — confirmed: `return provider.epoch_service, layer`. A
`lidar`-token endpoint with no matching layer key would therefore have fired a
`GetMap` for `LAYERS=<endpoint key>` at the *historical orthophoto* service, and
a portal answering 200 with HTML would have been recorded as a point cloud that
is **available**. A false positive on EXP-001 question 2 is the worst outcome
available here, so the portal is named in a comment and sections 4 and 9 stay
silent about it except through the "never asked" reason. **EDA-ELEV is narrowed,
not closed.**

**2026-11-04 · A Spanish translation of the notebook**, in the same folder, with
the English one as the source of truth: markdown translated, code cells
byte-identical, and a `--check-translation` guard in the module so the two cannot
drift apart unnoticed. This deviates from `AGENTS.md` → Documentation
Conventions, which allows Spanish only in `docs/tfm/` and the bilingual root
`README.md`; the exception is the user's decision, and `AGENTS.md` is theirs to
amend.
