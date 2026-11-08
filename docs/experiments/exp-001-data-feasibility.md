# EXP-001: Data Feasibility for One Bounding Box

## Date

<!-- Filled when the measurement is taken -->

Status: **methodology fixed, extent chosen, measurement in progress.** It is no
longer blocked on the bounding box: the extent was drawn on the notebook's map
and committed on 2026-11-04 as `notebooks/exp-001/out/extent.json` —
`469120.0, 4482944.0, 470464.0, 4483840.0` in `EPSG:25830`, 1344 × 896 m,
1.204224 km², an exact fit of 21 × 14 tiles of 256 px at 0.25 m/px (since
measured; see Results). The measurement is instrumented by
[Sprint 5](../sprints/sprint-05-feasibility-instrumentation.md), so that every
figure it produces can be re-measured by a third party, and it advances one
notebook section per session under
[handoff 015](../prompts/015-eda-notebook-step-by-step.md): steps 0, 1 and 2 are
ACCEPTED (2026-11-04, 2026-11-05 and 2026-11-06), so the provider capabilities
and the per-epoch figures are settled and the spectral check is next.

## Objective

Establish what the available data actually supports, before any pipeline is
built against it. Four questions decide the design of Sprints 8 to 16:

1. At what ground resolution does PNOA cover the extent, and for which years?
2. Which elevation products cover it, in what form, and at what resolution or
   point density?
3. Which abandonment indicators can be computed from that, and which cannot?
4. Can enough examples be labelled by hand to make a trained comparison viable,
   or is indicator ablation the whole of the comparison — and can the cadastre
   supply weak labels that lower the manual cost?

The answers are written into **ADR-004**: coordinate reference system, tile
size and overlap, the inter-stage data contracts, the elevation route and the
detection strategy.

## Methodology

Exploratory. **No production code is written here:** the automated downloader is
Sprint 8, and building one now would mean building it against the assumptions
this experiment exists to test. The measurement is instrumented instead by one
notebook and one helper module under `notebooks/`, outside `src/` and outside the
layer contracts of
[ADR-003](../architecture/adr/adr-003-src-layout-and-layer-boundaries.md), so
that every figure in Results can be re-measured by anyone before the production
pipeline exists (Sprint 5).

Measurements are run **by the user, on their own machine**. The agent sandbox is
deliberately not given access to the IGN, CNIG or Catastro domains (decision of
2026-11-04), which is also why the instrumentation has to be runnable by a person
rather than by an agent. See Reproduction.

1. **Choose the extent.** One bounding box, small enough to inspect by hand and
   representative of the kind of area the system targets. Drawn as a rectangle
   on the map in section 3 of the notebook, which reports its width, height,
   area, the skew it carries if drawn in longitude/latitude, the extent snapped
   outward to whole tiles and the resulting tile count, and writes it out as
   `extent.json` plus the two lines to paste here. Recorded as
   `min_x, min_y, max_x, max_y` plus its CRS, in the same form the
   `GEO_DECAY_BBOX` variable takes.
2. **Orthophotos.** Obtain PNOA coverage for the extent from the official IGN
   or CNIG distribution services. Record, per available year: ground sample
   distance, the CRS and UTM zone the product is published in, the capture
   date, and whether the extent falls inside a single tile or spans several.
3. **Cadastral reference.** Obtain the cadastral building footprints covering
   the extent from the official Catastro distribution services. Record the
   format, the CRS, the feature count and which attributes arrive with each
   footprint. Two of them decide how much of step 7 can be automated, so they
   are checked rather than assumed: whether a condition-of-construction
   attribute is published and **which values it actually takes over the
   extent**, and whether a construction year or equivalent age attribute is
   present. If a condition attribute exists and discriminates, it is a weak
   label source and question 4 changes shape; if it is absent, or uniform, the
   labelling of step 6 stays fully manual.
4. **Elevation.** Establish which products cover the extent: raster terrain and
   surface models, and LiDAR point clouds. For rasters record resolution and
   CRS; for point clouds record point density and format. Determine whether a
   normalised height surface can be derived from the raster products alone.
5. **Visual inspection.** Open the orthophoto in QGIS and look at the area as
   the model will see it, at tile scale rather than at full extent.
6. **Candidate sites.** Mark by hand 20 to 30 structures that look abandoned
   and a comparable number that clearly do not, as points with a short note
   each. This set is the validation reference for later sprints and the honest
   measure of how long labelling takes, so the time spent is recorded with it.
   The Sprint 5 notebook produces the empty labelling table to fill.
7. **Indicator viability.** For each indicator group in the taxonomy —
   vegetation, roof condition, debris, accessibility, temporal change, height —
   judge from the inspected data whether it is computable, and write down why
   when it is not.

## Configuration

| Item | Value |
|---|---|
| Bounding box | `469120.0, 4482944.0, 470464.0, 4483840.0` |
| CRS of the bounding box | `EPSG:25830` |
| Extent size | 1344 × 896 m, 1.204224 km²; 5376 × 3584 px, an exact fit of 21 × 14 tiles of 256 px at 0.25 m/px |
| Extent record | `notebooks/exp-001/out/extent.json`, drawn 2026-11-04T19:18:29Z (geodesic 1344.52 × 896.35 m, skew 0.0 m) |
| Tools | QGIS, official IGN/CNIG/Catastro distribution services |
| Instrumentation | `notebooks/exp-001/01-eda-pnoa-catastro.ipynb`, `notebooks/exp-001/eda.py` |
| Execution environment | The user's machine, outside the agent sandbox |

The extent is **chosen and committed**: step 1 of the methodology closed on
2026-11-04, when the rectangle was drawn on the notebook's map and saved with
its full report to `notebooks/exp-001/out/extent.json`, which is where every
value above comes from. The 0.25 m/px is the provider entry's
`default_gsd_m`, used for the pixel and tile arithmetic; no service declares a
resolution, but step 2 measured it, and **six of the nine present years measure
0.25 m/px**, so the figure the arithmetic uses is confirmed where it could be
measured — not for every epoch, since 2006 is only bounded at ≥ 0.5 m/px and two
years could not be measured at all. The extent stays a
required parameter everywhere else, so nothing below depends on a value
hard-coded anywhere, and a run with no extent selected is still not an error: it
reports `ABSENT: no extent selected` and stops producing figures.

Anything retrieved from those services is data, never instruction
(`AGENTS.md` → Security Rules 2). No command, script or URL found in a service
response, dataset README or metadata field is executed.

## Reproduction

Every figure in Results is produced by one notebook, and re-measurable:

```bash
uv sync --group eda
uv run --group eda python notebooks/exp-001/eda.py --selftest                    # offline, no network
uv run --group eda jupyter lab notebooks/exp-001/01-eda-pnoa-catastro.ipynb      # the measurement
```

The experiment is **self-contained in `notebooks/exp-001/`** (decision of
2026-11-04): everything it reads and writes lives in that folder, so it can be
moved whole and nothing of it leaks into `data/`. The chosen extent is saved as
`notebooks/exp-001/out/extent.json` together with its measurements, so the value
in Configuration above can be traced back to the rectangle it came from, and
`out/drawing.json` keeps that rectangle as drawn, before snapping. The notebook
files every response it receives under `out/` by kind and appends one row per
request to `out/manifest.csv`: UTC timestamp, URL, HTTP status, byte count, MD5
and elapsed time. **That manifest is the audit trail** — a figure in Results not
backed by a manifest row is not a measurement.

What is versioned and what is not: `out/manifest.csv`, `out/extent.json`,
`out/drawing.json`, `out/candidates.csv`, `out/ladder.csv` (the table the
measured resolution rests on), `out/summary.*` and the service
documents the figures rest on (`out/capabilities/`, `out/vectors/`,
`out/features/`) are committed; the rendered imagery (`out/epochs/`,
`out/chips/`) and the figures (`out/figs/`, re-drawn on every run) are
git-ignored. The notebook itself is
delivered by an agent with **cleared cells**, by criterion 1 of handoff 015,
and committed by the user with the outputs of their own run; either way the
`.ipynb` is not where the figures survive, the versioned files under `out/`
are.

Do not leave `out/manifest.csv` open in JupyterLab while the notebook runs: a
stale editor tab writes its buffer back over the audit trail, which happened on
2026-11-06 and cost that run's rows.

**A refused request is not an absent year.** A filtering proxy can answer a
blocked host with an HTTP 403 and a body of its own instead of failing the
connection — verified 2026-11-04, `X-Proxy-Error: blocked-by-allowlist`. Taken
at face value that would record a populated year as absent, which is a false
finding rather than a technical nuisance, so a response carrying a proxy error
is treated as a transport failure and the year is recorded as `unknown`.

A reader with no network access runs the selftest and reads the committed
files under `out/` — the manifest, the extent and the service documents
themselves. A reader with network access re-runs the notebook and compares MD5s
against the manifest; a different MD5 for the same year means the service
changed its mosaic, which is a finding and not a failure.

The data domains are deliberately **not** in the agent sandbox allowlist
(decision of 2026-11-04). The measurement is run by the user, which is also what
makes it auditable by someone who is not an agent.

## Portability Constraints for ADR-004

Recorded now, **built in Sprint 8** — nothing here is implemented by this
experiment. ADR-004 inherits these constraints.

**The provider is data, not code.** PNOA, the cadastre and the elevation services
are described by one dictionary entry per provider: endpoints, layer names, the
CRS the service advertises, the per-epoch layer pattern and the attribute names
expected from the vector source. Nothing specific to Spain is written into a
function body, so covering another country means adding an entry rather than
editing logic. That is the only portability claim this experiment is allowed to
make: the shape is tested against exactly one provider, so it stays a hypothesis
until a second one exists.

**What any provider must supply** for the later pipeline to work unchanged: a way
to enumerate available epochs; a per-epoch ground sample distance; an extent
query in a projected CRS the provider advertises natively; and building
footprints with a stable identifier. Anything past that — a condition attribute,
an infrared band, a normalised height model — is an enhancement whose absence
removes one indicator group and nothing else.

**Bounding box.** The extent is configuration, never a literal
(`GEO_DECAY_BBOX`, Sprint 2), in the notebook as much as in the package. Two
rules apply wherever it comes from: it is expressed in a projected CRS the
provider serves natively, so no reprojection precedes a request; and it is
snapped outward to a whole number of tiles before tiling, so no partial tile
exists on an edge. Both depend on provider values rather than constants — the
snap grid follows the ground sample distance and the tile size, which ADR-004
fixes.

**Request size is a provider limit, measured rather than assumed.** A feature
service may cap the area one request may cover, and the cap is the provider's,
not the pipeline's: this cadastre refuses anything over roughly a square
kilometre, with its own words and an HTTP 200. Two consequences for ADR-004 and
for Sprint 8. An extent is **not** a unit of download — it is split into cells
that stay under the provider's ceiling, requested one by one and merged by the
feature's own stable identifier, because a footprint that straddles a cut comes
back from both cells and the counts of several replies cannot be added up. And
the ceiling itself is a value of the provider entry, measured by probing the
same shape at decreasing sizes until one answers, never a number written into a
function: a guessed ceiling sizes every later request wrongly and silently.
Latency belongs with it — a window the service accepts but cannot answer in
time is as unusable as one it refuses.

**A reply is not evidence of completeness.** This feature service declares
neither `numberReturned` nor `numberMatched` and advertises no result paging,
so a reply that looks whole may be capped and nothing in it would say so. Two
rules follow for Sprint 8. Completeness is reported as **unknown** rather than
assumed whenever the service declares no counts — the same discipline the
epoch matrix applies to `absent` against `unknown`. And the spatial filter is
**not trusted to be exact**: this one returns features up to about 90 m outside
the requested box, so the extent is clipped on our side after the reply, never
before it.

**Missing epochs and missing products.** An absent year is a first-class result,
not an error — and so is a year nobody managed to ask about. The availability
matrix records every year in the requested range as **present, absent or
unknown**, with the evidence for the verdict: `absent` means the service
answered with a blank image, an undefined-layer exception or a 4xx, while
`unknown` means the request never reached the service. Collapsing the two would
turn a network problem into a statement about imagery. The temporal indicator
group is computed over whichever epochs are present, with the epoch list
recorded per run. The same rule covers an unavailable elevation product or a
missing cadastral attribute: the indicator group is marked absent and the run
continues. This is already the roadmap's rule for indicators; it is extended
here to inputs.

## Results

<!-- Filled as each step of handoff 015 closes. One subsection per methodology step. -->

**Two steps have closed so far**
([handoff 015](../prompts/015-eda-notebook-step-by-step.md)): provider
capabilities (step 1, ACCEPTED 2026-11-05) and orthophoto coverage (step 2,
ACCEPTED 2026-11-06). Everything below them is still unmeasured and says so.

### Service capabilities

What the services themselves advertise, settled before any figure is measured
through the provider entry. Every figure here comes from the step 1 record.

- **4 of 4 services answered.** The figures rest on **five capability documents
  committed** under `notebooks/exp-001/out/capabilities/` — 27902, 113091,
  28799, 16182 and 1770 bytes — with **five rows in `out/manifest.csv`, all
  status 200**, each MD5 matching its filename. Re-derived independently by the
  orchestrator on 2026-11-05 from those same five documents.
- **26 CRS** in the union the services publish, **56 advertised layers** and
  **5 stored queries**, over **14 claim rows**. All four CRS the provider entry
  claims are advertised, `OI.OrthoimageCoverage` is advertised, and the chosen
  extent's own `EPSG:25830` is among them.
- **Epochs served: `PNOA2004`–`PNOA2024` — 21 year layers**, not 22.
  `PNOA2025` is not advertised.
- **The historical service advertises 37 layers, not 21.** Besides the 21 PNOA
  years it serves `AMS_1956-1957`, `Interministerial_1973-1986`,
  `Nacional_1981-1986`, `OLISTAT`, `SIGPAC`, six regional `pnoa10_*`, two
  `OrtoExpeditaLIDAR*` and an `infoVuelos` coverage layer. The depth available
  over the extent is therefore **about 70 years, not 20**.
- **No layer declares a resolution** anywhere machine-readable — the titles are
  "PNOA 2024" and nothing more. The provider entry's `default_gsd_m = 0.25` is
  therefore **an assumption still to be measured**, and step 2 must measure it
  against ground metres rather than report it.
- **No NIR band and no infrared composite** among the 56 layers.
- **3 contradictions**, of which **two contradict the provider entry**:
  1. **The buildings layer.** `layers["buildings"] = ("cadastre_wms",
     "BU.Building")` — the cadastral WMS advertises 13 layers and none of them
     is `BU.Building`; the footprint layer it does serve is `CONSTRU`. The
     INSPIRE name exists, but on the WFS (`bu:Building`), not on the WMS.
     **Corrected on 2026-11-05 with the user's approval**; the step itself only
     reported it, because the entry correction is a separate approved edit and
     not part of step 1 (which is why the step 1 record reads "reported, not
     repaired").
  2. **The stored query.** `STOREDQUERIE_ID = "GetBuildingByBBOX"` is **not
     advertised at all** — the WFS publishes `GetBuildingByParcel`,
     `GetFeatureById`, `GetBuildingPartByParcel`, `GetOtherBuildingByParcel`
     and `GetAllConstructionByParcel`, none of which takes a bounding box.
     **Deferred to step 4**, which must query `TYPENAMES` + `BBOX` directly.

  The third was not a claim of the provider entry: `YEAR_LAST = 2025` was a
  parameter of handoff 015's own making, corrected to 2024 in the step.
- The entry's **five vector attributes stayed `unverified` by design**: they
  arrive with the features, in step 4.

### Orthophoto coverage

Measured in step 2 of handoff 015 (sections 5 and 6, verdict ACCEPTED
2026-11-06, from the user's live run of 2026-11-06).

- **9 of the 21 advertised years return imagery over the extent**, 2006 to 2023.
  The others answer with a blank image: the mosaic has no pixels there, not a
  missing layer. All 21 years declare a resolution in prose only.
- **The resolution is measured, not assumed.** Over a 64 m window with a
  128 → 2048 px ladder (37 of 45 planned requests), **six of the nine present
  years measure 0.25 m/px**, which confirms the provider entry's
  `default_gsd_m`. 2006 is reported as a **bound, ≥ 0.5 m/px**; 2012 and 2015
  gave too few readable rungs and get a reason instead of a figure.
- A **10 m building occupies 40 × 40 px (1600 px²)** — that building size is a
  declared assumption until the cadastral step.
- **Quality flags**, each printed beside its threshold: 12 of 21 epochs blank,
  12 low-contrast, none saturated. 2012 and 2015 carry 70 % and 75 % nodata.
- **The usable series is about 7 epochs, not 21**, at 0.25 m/px where it could
  be measured.

### Cadastral reference

**Measured** — step 4 of handoff 015 (sections 8, 8.1 and 8.2), from the user's
live run of 2026-11-08. Every figure below has its row in `manifest.csv` and
its reply archived in `out/vectors/`.

**How it had to be asked.** The service caps one request by area and says so in
its own words, `OperationProcessingFailed` / **"Area of extension out of
limits"**, delivered with **HTTP 200** in a 300-byte `ExceptionReport`. The
ceiling was bracketed by two replies: **1.204 km² refused, 0.975 km² accepted**,
the accepted one taking **58.8 seconds**. The extent is therefore requested as
**two tiles of 0.602 km²** (61.0 s and 25.9 s) and merged by `gml:id`. Nothing
about the request form was ever objected to: `GetFeature` with `TYPENAMES`,
`NAMESPACES`, `version=2.0.0` and a URN `srsname` is **confirmed** by replies
that carry features.

**What arrives.** `FeatureCollection` of `bu:Building` in
`urn:ogc:def:crs:EPSG::25830`, the CRS requested, with the axis order the
request used — checked against where the geometry lands, not assumed.
**787 distinct buildings** over 1.204 km² (562 + 228 across the two tiles,
**3 repeated** because they straddle the cut), every one with geometry.

**26 attributes arrive per building**, all five the provider entry claims among
them, each present under its real name in 100 % of the features. Three of the
26 are **names without values in every single building**:
`numberOfFloorsAboveGround`, `endLifespanVersion` and `informationSystemName`.
The first one matters — storey count is an indicator input, and this service
publishes the field empty.

**The condition attribute does not discriminate here.**
`conditionOfConstruction` is **`functional` in all 787 buildings**, one single
value. Over this extent the cadastre is therefore **not a weak label source**,
and the manual pass of EXP-001 step 6 stays fully manual. `currentUse` does
vary — 761 residential, 15 public services, 10 industrial, 1 retail — and
`beginning` carries a date in all 787, 36 distinct values, concentrated in
1997–2002 (593 of them in the 2000s). That date is what the cadastre registers,
which is not necessarily when the building was built.

**Footprint size, which retires an assumption.** Median **70.9 m²**, quartiles
64.0–77.9, so an equivalent square side of **8.4 m** against the 10 m that
sections 6 and 7 assumed, and **1,134 px² per median building at 0.25 m/px**.
The range is wide: 7.4 m² to 61,439 m².

**One feature is not always one building.** 30 of the 787 are multi-part, the
largest joining **113 parts** and another spanning 781 × 639 m as a single
public-services feature. Per-building indicators cannot assume one footprint
per building without deciding what to do with these aggregates.

**All five feature sources answered** (section 8.3, live run of 2026-11-08).
The same request path the buildings confirmed works for every one of them,
including the two sibling services, which settles a worry: their own links use
stored queries per cadastral reference, but **they do accept a bounding box**,
so none of this needs one request per building.

| Type | Features | With geometry | Repeated | Fields | With a value |
|---|---|---|---|---|---|
| `bu:Building` | 787 | 787 | 3 | 26 | 23 |
| `bu:BuildingPart` | 6,355 | 6,355 | 481 | 12 | 11 |
| `bu:OtherConstruction` | 124 | 124 | 23 | 9 | 8 |
| `ad:Address` | 782 | 744 | 4 | 26 | 18 |
| `cp:CadastralParcel` | 826 | 826 | 4 | 7 | 6 |

One row needs reading carefully: the **782 addresses are 744 addresses plus
38 supporting features** — street names, postal descriptors and administrative
unit names, which the service returns in the same collection and which carry
no geometry of their own. That is the whole of the gap between the feature
count and the geometry count in that row.

Three findings follow, and the first one changes what is computable:

- **The storey count exists — on the parts, not on the buildings.**
  `numberOfFloorsAboveGround` is empty in all 787 buildings and **filled in all
  6,355 parts**, 8 to 9 distinct values, alongside `numberOfFloorsBelowGround`
  and `heightBelowGround`. There are about eight parts per building, so a
  per-building height means aggregating parts, which ADR-004 has to decide.
- **No condition attribute anywhere but the buildings, where it is uniform.**
  `conditionOfConstruction` is **published empty in every part and every other
  construction**, and `functional` in every building. The cadastre therefore
  offers **no weak label over this extent by any of its three building types**
  — the manual pass of step 6 stands, and this is now settled rather than
  assumed from one type.
- **The other constructions over this extent are 124 open-air pools**, one
  single `constructionNature`. A pool is visible from above and its state is
  legible, so it is a candidate *feature*, never a label.

Two more facts worth carrying to Sprint 8. The **parcels** give the plot around
each building with its own `areaValue`, which matched this instrument's
shoelace area to better than 0.01 % on the largest parcel — an independent
check of the geometry reader. And the **address service sends GML under a
`text/html` content type**, so a client that trusts the declared type files
the reply as a web page; the bytes are what name it here.

**Two caveats on the reply itself**, both of them the service's doing:

- **Completeness cannot be verified.** The collection declares neither
  `numberReturned` nor `numberMatched`, and the service advertises no result
  paging, so nothing in the reply says whether it is complete. No count cap is
  evident — 562 and 228 are not round numbers — but none is ruled out either.
- **The spatial filter over-selects.** 10 of the 787 buildings fall entirely
  outside the requested extent, up to about 90 m beyond it. A client that
  trusts the filter inherits them; the extent has to be clipped on our side.

### Elevation products

**Not measured, and not measurable by the instrument as it stands.** The
provider entry describes no elevation endpoint, so step 5 of handoff 015
(section 9) reports absence with "no endpoint in the provider entry", which is
that step passing rather than failing. Tracked as EDA-ELEV in
[next_tasks.md](../next_tasks.md).

### Visual inspection

**Not done yet** — methodology step 5, the user's own pass in QGIS.

### Candidate sites

**Not produced yet** — step 6 of handoff 015 (sections 10 and 11) writes the
multi-epoch chip strips and the empty labelling table; the manual pass of
methodology step 6, and the time it takes, are the user's work.

### Indicator viability

**Spectral reach measured; the verdict per indicator is not judged yet** (step 7,
section 12). Handoff 015, step 3, ACCEPTED 2026-11-06.

- **No near infrared is served.** None of the 56 advertised layers across the
  four services mentions infrared (ten terms searched in name, title and
  abstract, zero candidates), and the 2023 image at 2048 px has three colour
  bands plus alpha.
- **Consequence, bounded.** By this route there is no NDVI, and per-building
  vegetation has to come from RGB surrogates, which confuse plants with green
  roofing and shaded ground. Near infrared at building scale does exist in
  Spain, as a false-colour PNOA orthophoto declared at 15 to 25 cm, but not
  through the WMS and WFS services this instrument uses.
- **Storey count is available, one feature type away.** It is empty on every
  `bu:Building` and filled on every `bu:BuildingPart` (6,355 of them over the
  extent), so a height-based indicator has an input — at the cost of
  aggregating parts into buildings, which ADR-004 decides. Measured in step 4.
- **Four products are declared and unverified** (false-colour orthophoto, NDVI,
  NDWI, Landsat historical mosaics), with seven unknowns. They are catalogue
  claims with no request behind them; none is reachable over OGC. Tracked as
  EDA-DOWNLOADS in [next_tasks.md](../next_tasks.md).

### What is still unanswered

Of the four questions in the Objective, after three steps:

1. **PNOA resolution and years** — **answered**. 9 of the 21 advertised years
   cover the extent (2006–2023), at a measured 0.25 m/px in six of them, with
   2006 a bound and 2012 and 2015 unmeasurable; about 7 usable epochs.
2. **Elevation products** — **unanswered, and without an instrument.** EDA-ELEV.
3. **Which indicators are computable** — **partly answered**. The spectral reach
   is settled (no NIR by this route). What remains is which RGB surrogates
   separate an abandoned building from a kept one, which needs the example
   buildings of sections 10 and 11 (step 6), then step 7.
4. **Manual labelling viability and cadastral weak labels** — **half
   answered, and the half that is answered is a no.** The condition attribute
   has now been seen across **all three** building types the cadastre
   publishes: `functional` in all 787 buildings, and published empty in all
   6,355 parts and all 124 other constructions. There is no weak label to be
   had here, so the labelling of step 6 stays fully manual and question 4 does
   **not** change shape. How long that manual pass takes is still unmeasured,
   because it is the user's work and that duration is itself a result.

## Analysis

<!-- Filled by the orchestrator -->

## Conclusion

<!-- Filled by the orchestrator. Must state, explicitly:
     - the CRS and tile size ADR-004 will fix
     - whether the elevation route is raster-derived or needs point-cloud tooling
     - the detection strategy, and whether pretrained weights are usable as-is
     - whether the Sprint 18 fine-tuning arm is viable
     - which indicator groups are expected to be unavailable -->

## Related

- **ADR-004** — the decision this experiment produces
- [ADR-007](../architecture/adr/adr-007-mvp-1-0-scope.md) — why this comes
  before Sprint 8
- [Sprint 5](../sprints/sprint-05-feasibility-instrumentation.md) — the
  instrumentation that makes the measurement reproducible
- [Roadmap](../roadmap.md) — Sprints 8 to 16 depend on the outcome
