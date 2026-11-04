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

<!-- `git rev-parse HEAD` immediately before launching; it must be the commit
     that carries handoff 013's accepted work -->

---

## Run Record

Date:
Tool and model:
Outcome: <!-- completed | failed | aborted -->

## Verification

Verdict: <!-- ACCEPTED | REJECTED -->
Files changed:
Gate:
Notes:
