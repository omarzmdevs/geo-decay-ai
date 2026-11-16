# ADR-004: CRS, Tiling, Data Contracts, Elevation Route and Detection Strategy

## Status

Proposed

## Date

2026-11-16

## Context

The GIS core (Block 3) cannot be built until five things are fixed: the
coordinate reference system, the tile geometry, the data contracts between
pipeline stages, the elevation route and the detection strategy. They are the
decisions most expensive to change later, because every stage after
acquisition depends on them. ADR-002 deferred them to a feasibility
experiment rather than deciding them up front.

That experiment is [EXP-001](../../experiments/exp-001-data-feasibility.md),
instrumented by Sprint 5 and concluded on 2026-11-16. It measured one extent
(`EPSG:25830`, 1.20 km²) through the providers' own services. The facts this
record rests on, all from EXP-001 → Results and Analysis:

- **Orthophoto.** 9 of 21 advertised years return imagery; 7 cover every
  example building at a measured **0.25 m/px**; 2006 is coarser and 2012 and
  2015 cover only part of the extent. Epochs are offset from the footprints by
  a metre or two in some years. Three colour bands, **no near infrared**.
- **Cadastre.** 787 footprints with stable identifiers, median 70.9 m²
  (about 8.4 m across, **about 34 px**); 26 compounds wider than a 64 m tile.
  The condition attribute is uniform, so the cadastre gives **no weak label**.
  The storey count is on the 6,355 building parts, not on buildings. The
  service caps a request near 1 km², declares no result counts, and its
  spatial filter over-selects by up to about 90 m.
- **Elevation.** Four rasters through two WCS 2.0.1 services: terrain and
  surface at 5 m, building and vegetation height at 2.5 m; one epoch, whole
  metres, resampled to the requested box. The LiDAR point clouds exist but
  were found only in a download portal with no automatable route.
- **Reference set.** The cadastre holds only registered buildings; seven
  manual samples, four outside the extent, are the route for the rest. No
  labels were produced, by the user's decision, and no detector was run.

EXP-001 also recorded portability constraints for Sprint 8 (Portability
Constraints for ADR-004); this record adopts them.

## Decision

### 1. Coordinate reference system

Every stage works in the **provider's native projected CRS**, read from the
provider entry and never written as a constant: **`EPSG:25830`** for the
Spanish provider and this extent. The extent is expressed in that CRS before
any request, so no reprojection precedes acquisition. An extent that leaves
the provider's zone states its CRS explicitly; a manual sample far outside the
zone returned no imagery in any year, which is the failure this rule prevents.

### 2. Tiling

- **256 px at the provider's ground sample distance**: at 0.25 m/px, a
  **64 m** tile, as used throughout EXP-001.
- The extent is **snapped outward to whole tiles** before tiling, so no
  partial tile exists on an edge.
- **Overlap of 40 px (10 m), adopted to be tested in Sprint 10**: it lets a
  building up to the upper quartile of footprint size fall whole inside at
  least one tile. Sprint 10 confirms or changes it, and records which.
- A tile is identified by its row and column from the snapped origin.
- Structures wider than one tile are handled as **entities**, not tiles
  (section 5).

### 3. Elevation route

**Raster-derived, through the WCS services**, for MVP 1.0: building height and
vegetation height at 2.5 m, terrain and surface at 5 m, under the limits EXP-001
measured — one epoch, whole metres, cells resampled to the requested box
(EDA-WCSGRID). This supports one height per entity and nothing finer: no roof
geometry and no height change over time.

**LiDAR point clouds remain the elevation architecture's extension for a later
version of the project**, not a discarded option. They would add roof geometry
and denser height, at the cost of the download route EXP-001 did not find and
of PDAL. PDAL is therefore **not part of MVP 1.0**, and the container image
needs only GDAL for elevation.

### 4. Data contracts between stages

Each contract is a structure in the **domain layer**, with no I/O
(ADR-003); the data layer reads and writes it. Between stages they travel as
files, since the spatial database is deferred (ADR-007): **GeoParquet** for
entities, indicator results and indices, **GeoTIFF** for rasters and tiles.

| Contract | Carries |
|---|---|
| **Extent request** | four coordinates, CRS, provider key, the extent snapped to tiles |
| **Acquisition record** | one row per request — URL, status, checksum, stored file, time, error; per epoch a verdict **present, absent or unknown** with its evidence; completeness **unknown** when the service declares no counts |
| **Epoch** | provider, year, layer, CRS, ground sample distance **measured or declared** (and which), no-data share, **alignment status** |
| **Tile** | tile id (row, column), bounds, CRS, size in pixels, overlap, epoch |
| **Entity** | stable id, **source** (`cadastre`, `detector` or `manual`), geometry, CRS, area, number of parts, storeys, height |
| **Indicator result** | entity id, indicator group, value, status **available, absent or unknown**, reason, epochs used |
| **Index** | entity id, score, per-indicator contributions, absent groups |

Rules the contracts carry:

- **Entity identity.** The cadastral reference for registered structures;
  `M-NNNN` for manual samples, as in EXP-001; for detections, an id derived
  from the run and the detection's position, in a namespace that cannot
  collide with the other two. The source is always recorded, so the bias
  toward registered buildings stays measurable.
- **Storeys from parts.** A cadastral entity's storey count is the **maximum
  over its building parts**, and the number of parts is kept beside it.
- **Epoch alignment is required before any comparison across years.** EXP-001
  saw offsets of one to two metres between epochs. The method is Sprint 9's to
  choose; the epoch contract records the result, and a temporal indicator
  refuses unaligned epochs.
- **Absence is a value.** A missing epoch, product or attribute removes the
  indicator group that needs it, recorded as absent with its reason; it never
  blocks the run.
- **Clipping is ours.** A feature service's spatial filter is not trusted;
  replies are clipped to the extent after arrival.

### 5. Detection strategy

**Two routes**, by the user's decision of 2026-11-16:

- **Registered structures** become entities directly from the **cadastral
  footprints**, cropped per footprint as EXP-001's strips were. No detector is
  needed for what the cadastre already locates.
- **Unregistered structures** are sought with a **pretrained detector used
  without retraining**, and validated against the manual samples.

**Whether pretrained weights are usable as-is is not measured.** EXP-001 ran no
detector; the objects are small (about 34 px) and colour-only. Sprint 11,
reduced, tests the chosen pretrained model on the labelling table before
Sprint 12 relies on it.

### 6. Fine-tuning arm (Sprint 18)

**Viable, by the user's decision of 2026-11-16.** The manual labels it needs
are produced before that sprint; the cadastre provides none. The cost of
labelling per building was not measured, so Sprint 18 depends on that manual
pass being scheduled ahead of it.

### 7. Portability

The constraints recorded in EXP-001 are adopted as rules for Sprint 8: the
provider is **data, not code** (one entry per provider: endpoints, layers,
native CRS, epoch pattern, attribute names, request ceiling); the request
ceiling is **measured**, never assumed, and an extent is split into cells
under it and merged by the feature's own id; and a reply is not evidence of
completeness.

## Alternatives Considered

- **A web CRS (EPSG:3857) or geographic coordinates for every stage.** Rejected:
  metres would be distorted, and every request would need a reprojection the
  provider does not serve natively.
- **Larger tiles (512 px).** Not chosen: a 34 px building is a smaller share of
  the tile, and EXP-001's whole measurement used 256 px. Sprint 10 may revisit
  it with the overlap.
- **Point-cloud elevation now.** Deferred to a later version: no automatable
  route was found, it needs PDAL, and the rasters already answer how tall a
  structure is.
- **One detector for everything.** Rejected for MVP 1.0: it would spend the
  detector's error budget re-finding what the cadastre already gives with
  exact geometry and stable ids.
- **Cadastre only, no detector.** Rejected: it cannot see unregistered
  structures, which are the ones the project most wants to find.
- **Sprint 18 dropped and the comparison reduced to indicator ablation.**
  Considered and set aside by the user's decision; ablation remains Sprint 19's
  minimum.
- **GeoPackage between stages.** Not chosen: easier to open in QGIS, worse for
  column-wise work on many entities. QGIS reads GeoParquet as well.

## Consequences

**Positive.**

- Block 3 can be planned: Sprints 8 to 10 have a CRS, a tile, contracts and an
  elevation route to build against.
- The elevation route needs no new system dependency; the container stays
  GDAL-only for MVP 1.0.
- Registered structures arrive with exact geometry and stable ids, so the
  detector's measured quality concerns only what the cadastre misses.
- Every input that can be missing has a recorded status, so a partial provider
  degrades indicator by indicator instead of failing.

**Negative.**

- No roof geometry and no height change in MVP 1.0; vegetation without near
  infrared relies on RGB surrogates.
- The detector route rests on an untested assumption until Sprint 11.
- Sprint 18 depends on a manual labelling pass whose cost is unknown.
- Epoch alignment adds a processing step to Sprint 9 before any temporal
  indicator exists.
- Two entity sources mean two code paths into the same contract, and a
  deduplication rule where a detection falls on a cadastral footprint, which
  Sprint 13 must define.

**Follow-ups.** EDA-WCSGRID (snap WCS requests to the coverage's native grid)
and EDA-DEDUP (store a reply only when no equivalent one exists) are carried
into Sprint 8; EDA-DOWNLOADS (point clouds, false-colour orthophoto) into the
later version that adds LiDAR.
