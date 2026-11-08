# Next Tasks

> The active slice of the plan. The full block and sprint structure lives in
> [roadmap.md](roadmap.md), which is the operational source of truth.
> Updated at the end of every sprint.

The executed subset of the plan is MVP 1.0
([ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)); the per-sprint status
table is in [roadmap.md](roadmap.md).

## Active Sprint

- [ ] **Sprint 5 · Feasibility Instrumentation** (gate of Block 3) — make
  [EXP-001](experiments/exp-001-data-feasibility.md) measurable, and
  re-measurable by a third party: one helper module and one notebook under
  `notebooks/`, outside `src/`, measuring PNOA epoch availability and image
  quality, the cadastral footprints and the attributes that arrive with them,
  and the availability of the elevation products, and writing the empty
  labelling table for the manual pass. Planned in
  [sprint-05-feasibility-instrumentation.md](sprints/sprint-05-feasibility-instrumentation.md)
  with handoffs [013](prompts/013-eda-toolkit-and-provider-config.md) and
  [014](prompts/014-eda-notebook.md). 014's deliverable was discarded by the
  user on 2026-11-04 and replaced by
  [015](prompts/015-eda-notebook-step-by-step.md), which rebuilds the notebook
  one section at a time, in Spanish, each section confirmed against the live
  services before the next is written. It occupies the slot
  left free by the deferral of Sprint 5 · DVC
  ([ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md) amendment 2026-11-04).

  Two things stay deliberately outside the agents. The **data domains are not
  added to the sandbox allowlist** (2026-11-04), so the measurement is run by
  the user and every acceptance criterion is offline. And the **manual labelling
  pass** (EXP-001 step 6) is the user's work, because how long it takes is
  itself one of the results.

- [ ] **Feasibility experiment → ADR-004** — measure what the data supports for
  one bounding box: PNOA resolution and available years, the cadastral
  footprints and the attributes that arrive with them, which elevation products
  exist for the extent and in what form, and a manually located set of candidate
  sites to reuse as a validation reference. ADR-004 follows from it, is required
  before Sprint 8, and also decides the elevation route (Sprint 9), the detection
  strategy (Sprints 11–12) and whether the fine-tuning arm of Sprint 18 is
  viable. Methodology in
  [exp-001-data-feasibility.md](experiments/exp-001-data-feasibility.md);
  the extent is chosen and committed since 2026-11-04 (`EPSG:25830`, 1.20 km²,
  in `notebooks/exp-001/out/extent.json`), so the measurement is no longer
  blocked: it advances one notebook section per session. Instrumented by
  Sprint 5 above;
  the Analysis, the Conclusion and the two `docs/research/` documents are the
  orchestrator's, written from whatever the user's run measures.

Completed sprints of Block 1: Sprint 1 · Foundations and Quality Gate
(2026-10-14, [log](sprints/sprint-01-foundations.md)), Sprint 2 · Runtime
Foundations (2026-10-21, [log](sprints/sprint-02-runtime-foundations.md),
handoffs 007 and 008 ACCEPTED) and Sprint 3 · CI/CD (2026-10-25,
[log](sprints/sprint-03-cicd.md), handoff 009 ACCEPTED). Block 1 closed 2026-10-25.

## Completed Sprints

- [x] **Sprint 4 · MLflow** (Block 2) — experiment tracking in place before the
  first experiment exists: a tracking port in the domain, an MLflow adapter
  confined to the data layer, a null adapter, and composition in delivery with
  the store addressed by a configuration string. Reduced by
  [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md) to a local file store;
  the decisions are in
  [ADR-008](architecture/adr/adr-008-experiment-tracking.md). Logged in
  [sprint-04-mlflow.md](sprints/sprint-04-mlflow.md): handoffs
  [010](prompts/010-experiment-tracking-port-and-config.md),
  [011](prompts/011-mlflow-adapter-and-import-contract.md) and
  [012](prompts/012-tracking-composition-and-cli.md) ACCEPTED 2026-10-27, each
  committed separately. The only sprint of Block 2 that MVP 1.0 executes, so
  Block 2 closed with it on 2026-10-27.

- [x] **Sprint 3 · CI/CD** (Block 1) — the ADR-005 gate runs on GitHub
  Actions for every push and every pull request to `main`, through the same
  `.pre-commit-config.yaml` the commit hook uses, so the gate keeps one
  definition. Reduced by [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)
  to one workflow running the gate; the image build and CD stay out
  (amendment 2026-10-21). Logged in
  [sprint-03-cicd.md](sprints/sprint-03-cicd.md): handoff
  [009](prompts/009-ci-quality-gate-workflow.md) ACCEPTED 2026-10-21, run
  interactively because `.github/workflows/**` is protected. Closed 2026-10-25
  on the first green run on GitHub (run #2, `d061937`, `success`), per the
  handoff's `## Sprint Closing Evidence`.

## Blocked On

- [x] **The bounding box to study** — the measurement cannot produce a figure
  without it, and it is the user's choice. Section 3 of the Sprint 5 notebook is
  what closes it: a map with a rectangle tool that reports width, height, area,
  the skew a longitude/latitude rectangle carries in the projected CRS, the
  extent snapped outward to whole tiles and the resulting tile count, and the
  two `GEO_DECAY_*` lines to paste into EXP-001 → Configuration. **Resolved
  2026-11-04**: the user drew it and it is committed as
  `notebooks/exp-001/out/extent.json` — `EPSG:25830`, 1344 × 896 m, 1.204224
  km², an exact fit of 21 × 14 tiles — and recorded in
  [EXP-001](experiments/exp-001-data-feasibility.md) → Configuration.

Resolved earlier, kept for traceability:

- [x] `AGENTS.md`, `.agents/roles/developer.md` — Black replaced by Ruff format;
  import-linter added to the gate.
- [x] `.agents/TOOLING.md` — developer launch allowlist uses `Bash(uv run *)`.
- [x] `.agents/policy.yaml` — developer scope gains `uv.lock`, `.python-version`,
  `tests/acceptance/.gitkeep`.
- [x] `.claude/settings.json` — sandbox network allowlist for PyPI and Python
  downloads.
- [x] Infrastructure deny entries lifted for the interactive session of
  handoffs 002 and 004 (per session, not in the shared settings).
- [x] uv installed on the host.

## Next Up

- [ ] **Block 3 · GIS Core** — Sprints 7–10. Sprint 7 (spatial database) is
  deferred by ADR-007; Sprints 8–10 (data download, GIS processing, tiling) all
  depend on ADR-004, so the block cannot be planned until the feasibility
  experiment above has run. Block 2 needs no further planning: DVC is deferred
  and Sprint 6 is absorbed into Sprint 2, so it closes with Sprint 4.

## Governance and Architecture Debt

Tracked findings from the project review, deferred with their identifiers:

- [x] **E6 · ADR-003** — `src/` layout and layer boundaries (2026-10-08).
- [ ] **E5 · ADR-004** — CRS, tiling and data contracts, plus the elevation
  route and the detection strategy. Required before Block 3. Now written from
  the feasibility experiment above rather than decided up front.
- [x] **E5 · ADR-005** — dependency manager (2026-10-08).
- [x] **E1 · Write-scope enforcement** — `scripts/policy_guard.py` validating the
  working-tree diff against `.agents/policy.yaml`, plus its pre-commit hook. Scheduled in Sprint 1.
  Guard done (handoff 003, ACCEPTED 2026-10-12); pre-commit hook done (handoff 004, ACCEPTED 2026-10-12).
- [ ] **PDAL · System-level PDAL** — no current Debian/Ubuntu ships it; deferred
  from Sprint 1 to Sprint 9, built from a pinned source release
  (ADR-005 amendment 2026-10-14). Whether it is needed at all is now decided by
  ADR-004: the raster elevation route requires only GDAL
  (ADR-005 amendment 2026-10-15).
- [x] **RUFF-ISORT · `known-first-party` is now declared** — ruff's heuristic
  classified `geo_decay_*` as third-party while the packages held only
  `__init__.py` and as first-party once a module existed, so it demanded
  opposite import grouping before and after handoff 007. Declared explicitly in
  `pyproject.toml` on 2026-10-16.
- [ ] **CI-IMAGE · The Docker image is not built in CI** — out of Sprint 3 by
  ADR-007 (amendment 2026-10-21): the DevContainer builds it daily, so a CI
  build would spend minutes on GDAL to repeat a signal already available. It
  enters CI as a paths-triggered workflow (`Dockerfile`, `docker-compose.yml`,
  `.devcontainer/**`, `pyproject.toml`, `uv.lock`) the moment that stops being
  true.
- [ ] **PORT-RUNID · The tracking port exposes no run identifier** —
  `ExperimentTracker.start_run` yields `None`, so a caller cannot cross-
  reference a run with an experiment record in `docs/experiments/`. Handoff 012
  logs the experiment name instead of the run id rather than import `mlflow`
  into delivery to obtain it
  ([012](prompts/012-tracking-composition-and-cli.md), verification notes).
  Decide in Sprint 12, when the first real experiment needs that link: either
  the context manager yields a run id or the port gains a `current_run_id`.
- [ ] **MLFLOW-STORE · The MLflow file store is in maintenance mode** — MLflow
  3.17.2 refuses to construct a `FileStore` without
  `MLFLOW_ALLOW_FILE_STORE=true` and names `sqlite:///mlflow.db` plus
  `mlflow migrate-filestore` as the supported destination. Sprint 4 opts in,
  inside the adapter, rather than carrying the database and dataframe stack
  eight sprints before its consumer
  ([ADR-008](architecture/adr/adr-008-experiment-tracking.md), amendment
  2026-10-27). `mlflow-skinny` cannot use a database backend at all — verified,
  not assumed — so the migration changes the distribution as well as the URI.
  Trigger: Sprint 12, the first real experiment, or any MLflow version bump,
  whichever comes first. Expect
  `test_a_non_file_uri_fails_with_the_vendor_error` to fail when the
  distribution is swapped: it asserts skinny's rejection of a `sqlite:` URI on
  purpose, as a tripwire, and is not a regression.
- [x] **CI-PIN · GitHub Actions pinned by tag, not by commit SHA** — resolved
  2026-10-25 in `d061937`: `actions/checkout` and `astral-sh/setup-uv` carry a
  commit digest with the version in a trailing comment, and both move together
  on a bump. Digest-pinning the container base image is a separate matter, under
  Known Issues in [current_state.md](current_state.md).
- [x] **TOOL-VERIF · `.agents/TOOLING.md` → Pending Verification was stale** —
  updated by the user on 2026-10-25: `dontAsk` (handoffs 007 and 008), the uv
  cache (`[tool.uv] cache-dir`, commit `dc769b9`) and the W2 and W3 results now
  sit in a new `## Verified` section. One honest unknown stays there, sandbox
  compatibility with Docker and package installation, to be confirmed from a
  container build or dropped.
- [x] **W2 · Secret pattern drift** — closed 2026-10-25 as resolved by design.
  The enumerated deny list exists to keep `.env.example` readable, since a deny
  rule cannot carve an exception, while the full `.env.*` glob is enforced by
  the working-tree guard from `secrets.include` (checked: `.env.staging` and
  `.env.whatever` classify as SECRET, `.env.example` does not). A missing deny
  entry costs a tool-level deny, never the guard's check. Stated in
  `.agents/TOOLING.md`.
- [x] **W3 · Permission coverage** — answered 2026-10-25: an `Edit(...)` deny
  does cover file writes. With `Edit(./.claude/**)` in the deny list and no
  `Write` rule, a `Write` to `.claude/skills/project-status/SKILL.md` was
  refused, and the shell route was refused by the sandbox as well. Recorded in
  `.agents/TOOLING.md` → `## Verified`.
- [x] **W12 · Redundant rule** — `Bash(git commit*--no-verify*)` was covered by
  the broader `Bash(git commit*)`; removed from `.claude/settings.json` by the
  user on 2026-10-25.

- [ ] **EDA-ELEV · The provider entry describes no elevation service** — so
  EXP-001 question 2 (which elevation products cover the extent, in what form)
  **cannot be answered by the instrument as it stands**. `PROVIDERS["es-pnoa"]`
  holds `ortho`, `ortho_history`, `cadastre_wms` and `buildings_wfs` and nothing
  else, a gap in handoff 013's specification of the entry rather than a finding
  about coverage. Section 9 of the notebook already discovers elevation services
  generically, by token in the entry's logical keys, and reports one row per
  product category, so it starts probing with no change to the notebook the
  moment an entry gains one. Found verifying handoff 014, note 3.

  **Narrowed 2026-11-04**, on the user's decision to add the endpoints as a
  labelled hypothesis: the entry gained an INSPIRE elevation (MDT) WMS and a
  terrain layer name, both marked unconfirmed in the data. **Reopened in full
  2026-11-05**: that addition was part of handoff 014's discarded deliverable
  and went with the user's revert, so `PROVIDERS["es-pnoa"]` again holds only
  `ortho`, `ortho_history`, `cadastre_wms` and `buildings_wfs`, and step 5 of
  handoff 015 will report absence with "no endpoint in the provider entry".
  Also open, and never addressed: the **surface model and the point cloud**,
  which come from the CNIG download portal. That portal is deliberately not an
  endpoint — it has no OGC interface, and because `_resolve_layer` sends an
  unknown layer name to the `epoch_service`, a lidar-token endpoint would have
  fired a `GetMap` at the historical orthophoto service and could have recorded
  the point cloud as *available*. Probing downloads needs either a `downloads`
  field on `Provider` or a change to section 9, neither of which is authorised
  yet. Until then EXP-001 question 2 is answerable only in part.
- [ ] **EDA-DOWNLOADS · Three datasets are blocked on the same missing route** —
  the instrument speaks WMS and WFS, and the three datasets that would answer
  open questions are none of those: the **lidar** that EXP-001 question 2 needs
  (EDA-ELEV), the **Sentinel index products**, and the **PNOA false-colour
  infrared orthophoto** at 15 to 25 cm, which is the only declared route to
  near infrared at building scale and therefore the only one that would put
  NDVI back on the table. All three are files in a download catalogue; section 7
  records them as declarations with their unknowns.
  What would unlock all three at once is a second access route on `Provider`:
  a direct URL read by **HTTP range**, which a COG supports, so one bounding box
  can be taken out of a national sheet without downloading it. For Sentinel it
  would also need a catalogue search by bbox and date; an external report names
  the Copernicus Data Space STAC, the Sentinel Hub Process API (OAuth) and the
  public STAC catalogues of AWS and Microsoft as candidates, **none of them
  verified** — they are leads from fetched content, not endpoints, and nothing
  enters `PROVIDERS` until a request of ours is answered and leaves a manifest
  row.
  **Measure this one first**: whether the catalogue's COG files have a stable
  direct URL that honours a range request. One `HEAD` and one ranged `GET`
  settle it, it is the cheapest of the three, and if the answer is no then whole
  sheets are the only option and the cost of every one of these products changes
  completely. Raised 2026-11-06 writing section 7.

- [x] **EDA-WFSAREA · The cadastral WFS caps the area of one request** —
  **measured and closed 2026-11-08.** The ceiling is bracketed by two replies
  of the service's own: it refused 1.204 km² with `OperationProcessingFailed`
  and **"Area of extension out of limits"**, delivered as **HTTP 200** in a
  300-byte `ExceptionReport`, and accepted 0.975 km², taking 58.8 seconds over
  it. The accepted figure is now `wfs_max_area_km2` in the provider entry and
  the extent is requested as two tiles merged by `gml:id`. Two things stay with
  it: the consequence is recorded in
  [EXP-001](experiments/exp-001-data-feasibility.md) → Portability Constraints
  for ADR-004 and Sprint 8, and the wait is a provider value too
  (`wfs_timeout_s`, 120 s), because 30 s turned a slow service into an
  apparently broken one.

- [ ] **EDA-WFSTRUST · The feature reply cannot be checked, and the filter
  over-selects** — two separate things the same run found, both the service's
  doing. The collection declares neither `numberReturned` nor `numberMatched`
  and the service advertises no result paging, so **nothing in a reply says
  whether it is complete**; 562 and 228 features are not round numbers, which
  argues against a cap without ruling one out. And **10 of the 787 buildings
  fall entirely outside the requested extent**, up to about 90 m beyond it, so
  the bounding-box filter is approximate. The notebook already reports both
  rather than hiding them — "sin declarar" instead of "no truncada", and a
  count of footprints outside the extent. What is open is the pipeline rule:
  Sprint 8 clips on our side after the reply and treats completeness as
  unknown. Raised 2026-11-08, step 4 of handoff 015.

- [x] **EDA-BUTYPES · Only one of the three feature types has been asked for**
  — **closed 2026-11-08, all five sources answered.** `bu:BuildingPart`
  (6,355), `bu:OtherConstruction` (124), `ad:Address` (782) and
  `cp:CadastralParcel` (826) join the 787 buildings, every one of them over
  the same tiles and through the same request path, which also settles that
  the two sibling services **do accept a bounding box** rather than only the
  per-reference stored queries their links use. The findings are in
  [EXP-001](experiments/exp-001-data-feasibility.md) → Cadastral reference:
  the storey count is empty on buildings and filled on all parts; the
  condition attribute is empty on parts and other constructions, so the
  cadastre offers no weak label by any of its three building types; and the
  other constructions over this extent are 124 open-air pools. Two
  consequences stay open for ADR-004 rather than for this experiment: how a
  per-building height is aggregated from about eight parts, and whether the
  parcel is the right unit for a vegetation indicator.

- [ ] **EDA-CTYPE · A service labels GML as `text/html`** — the cadastral
  address service sends a feature collection under a `text/html` content
  type. The instrument now names a body after its bytes rather than after the
  declared type, so the reply is filed as `.xml` and parses, but the lesson
  belongs in Sprint 8: **a declared content type is a claim like any other**,
  and a download route that dispatches on it will mis-handle this provider.
  Found 2026-11-08, step 4 of handoff 015; the two replies already on disk
  carry the old `.html` name.

- [ ] **EDA-JUMP · The resolution table prints a meaningless jump factor** —
  section 6 reports, beside each measured resolution, the factor by which the
  detail residual jumps between rungs. Past the flattening point that residual
  is numerically zero (order 1e-15), so the factor comes out of order 1e13 and
  reads as a broken number. The verdict does not use it — the detail floor
  does, and the floor-sensitivity sweep in `--selftest` covers that — so this is
  presentation, not a wrong measurement. Fix by reporting the residuals and the
  floor and dropping the ratio, or by showing the ratio only while both terms
  are above the floor. Found verifying step 2 of handoff 015, 2026-11-06.

- [ ] **EDA-WMSVER · The map's orthophoto layer ignores the provider's WMS
  version** — `ipyleaflet.WMSLayer` (0.20.0) exposes no `version` trait, so the
  browser requests tiles at the library's default WMS version rather than the
  entry's `wms_version` (`1.3.0`), and a URL-embedded `VERSION` would collide
  with the one Leaflet appends. Consequence for reading the map: error or blank
  tiles under the selector mean *either* a wrong layer name *or* a version
  mismatch, so section 4's `GetCapabilities` is what distinguishes them. Recorded
  as a code comment in the notebook's map cell. Closes if a later ipyleaflet
  exposes the trait, or by serving the preview through a tile endpoint that pins
  the version.
- [x] **EDA-OSERROR · A failed request could leave no manifest row** —
  `fetch` caught `requests.RequestException`, which is a *subclass* of `OSError`
  rather than the reverse, so a bare `OSError` raised inside `requests` escaped
  the handler that writes the manifest row. The experiment's audit trail was
  therefore silently incomplete, against criterion 5 of handoff 013. Not
  hypothetical: an unreadable CA bundle made two `https://www.ign.es` requests
  vanish from `manifest.csv` during the handoff 014 verification run. Resolved
  2026-11-04, on direct instruction without a handoff: the handler covers both
  exceptions and the selftest now drives a bare `OSError` through `fetch` with a
  non-existent `REQUESTS_CA_BUNDLE` and asserts that a row is written.
  Re-verified independently — nothing raised, `status` 0, one manifest row with
  its `error` column set.

  The lesson behind it stays open, alongside [EDA-GSD]: **handoff 013's criterion
  5 was checked only against a `RequestException`**, so the selftest could not
  have caught this. A contract that says "never raises" needs a check per failure
  *class*, not one representative failure.

- [x] **EDA-GSD · A provider value sat in a function default** — `save_extent`
  in `notebooks/eda_helpers.py` defaulted to `gsd_m=0.25`, the PNOA ground sample
  distance. Criterion 3 of handoff 013 keeps hosts, layers and attributes inside
  the `PROVIDERS` entry, but its token list cannot catch a number, so this one
  got through: for a provider at another resolution the pixel and tile figures
  would have been silently wrong rather than absent. Resolved 2026-11-04 —
  `save_extent` and `extent_report` both require `gsd_m` and `tile_px` now, and
  the selftest reads the value from `PROVIDERS["es-pnoa"].default_gsd_m`. Fixed
  on direct instruction without a handoff; the deviation and the re-verification
  are recorded in
  [handoff 013](prompts/013-eda-toolkit-and-provider-config.md) → Verification,
  note 3.

  The general lesson stays open: **criterion 3's guard is textual, so no numeric
  provider value is protected by it.** Any later provider-specific number — a
  resolution, a tile size, a pixel limit, a maximum feature count — can slip into
  a signature the same way. Sprint 8 inherits the problem together with the
  constraints in EXP-001 → Portability Constraints.
- [ ] **SANDBOX-SYNC · A plain `uv sync` cannot prune the `eda` group** — it has
  to delete `.venv/lib/python3.12/site-packages/tornado/test/test.key`, which the
  agent sandbox denies along with every other `*.key`. Verified 2026-11-04. Any
  verification command that syncs the `eda` group away must run with
  `UV_PROJECT_ENVIRONMENT` pointed at a temporary directory, as handoff 013's run
  did; bypassing the sandbox is not the answer, since the deny rule is doing its
  job and only happens to catch a test fixture. Closes if the group stops pulling
  tornado in, or if deletions inside `.venv` become permitted.
- [ ] **EDA-PROV · The provider shape is tested against one provider** — the
  portability claim of EXP-001 is that a provider is one dictionary entry
  (endpoints, layer names, advertised CRS, epoch layer pattern, expected vector
  attributes) and that nothing country-specific sits in a function body. It is
  exercised by exactly one entry, `es-pnoa`, so the shape stays a hypothesis.
  Trigger: the first non-Spanish provider, or Sprint 8, whichever comes first —
  Sprint 8 is free to discard the exploratory module and keep only the
  constraints recorded in EXP-001 → Portability Constraints for ADR-004.

## Backlog

- [ ] Research state-of-the-art for abandoned infrastructure detection (Sprint 11;
  in MVP 1.0, to the depth the ADR-004 strategy decision needs).
- [ ] Evaluate PNOA/LiDAR data sources and download APIs (Sprint 8; first pass in
  the feasibility experiment above).
- [ ] Define abandonment indicators taxonomy (Sprint 14).

## Last Updated

2026-11-05
