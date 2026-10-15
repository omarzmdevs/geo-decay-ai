# ADR-005: Dependency and Environment Manager

## Status

Accepted

## Date

2026-10-08

## Context

Sprint 1 creates `pyproject.toml`, the container images and the quality gate.
All three depend on how Python, dependencies and tools are installed and
locked, so the manager must be chosen first.

Constraints:

- **Reproducibility is a thesis requirement.** Every experiment must be
  re-runnable from a locked environment.
- **GDAL and PDAL are C libraries** installed at system level in the container
  ([architecture.md](../architecture.md) → Deployment). Python bindings that
  link to them must match those versions; wheels that bundle their own copy of
  GDAL or PROJ can silently diverge from the system one.
- **Agents run the gate on the host** (macOS) as well as in the container, so
  the gate must work outside the container for code that does not touch GIS
  libraries — which ADR-003 guarantees for the domain.
- **The stack listed Ruff and Black side by side.** Ruff's formatter is
  Black-compatible, so running both formats every file twice and invites
  conflicts.

## Decision

**uv manages Python, dependencies and the lockfile.**

- **Python 3.12**: `requires-python = ">=3.12,<3.13"`, plus a `.python-version`
  file. Mature support across the geospatial and ML stack (Rasterio, PDAL,
  PyTorch). uv installs the interpreter, so the host Python version is
  irrelevant.
- **`pyproject.toml` (PEP 621)** is the only manifest. Runtime dependencies in
  `[project.dependencies]`; development tools in `[dependency-groups]` (PEP 735),
  group `dev`.
- **`uv.lock` is committed** and is the single source of every version,
  including the gate tools.
- **Build backend: hatchling**, listing the four packages of ADR-003 explicitly.

**Quality gate.** All tool configuration lives in `pyproject.toml`; every tool
runs through `uv run`, so it uses the locked version:

| Tool | Role | Replaces |
|---|---|---|
| Ruff (`ruff check`) | Linting, import sorting, TID252 | — |
| Ruff (`ruff format`) | Formatting | **Black, removed from the stack** |
| MyPy (`--strict`) | Type checking of `src/`, `tests/`, `scripts/` | — |
| import-linter (`lint-imports`) | Layer contracts of ADR-003 | — |
| Pytest | Unit and acceptance tests | — |
| pre-commit | Runs the gate on commit | — |

The gate command, used by handoffs as the base of every verification command:

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy \
  && uv run lint-imports && uv run pytest
```

**pre-commit uses local hooks** (`repo: local`, `entry: uv run ...`) rather than
pre-commit's own remote hook repositories. Tool versions therefore come from
`uv.lock` alone, and pre-commit does not download a second copy of each tool.

**GIS libraries.** The container image is the reference environment. GDAL and
PDAL are installed at system level, and Python bindings that link to them
(`gdal`, `pdal`) are pinned to the system library version. Whether Rasterio,
Fiona and pyproj also build from source against the system GDAL/PROJ, or use
their bundled wheels, is decided when the GIS core is built (Block 3), together
with ADR-004; Sprint 1 only installs the system libraries and proves they load.

## Amendment 2026-10-14 · PDAL Deferred to Block 3

Handoff 002 showed that no current Debian or Ubuntu release ships PDAL:
`pdal` and `libpdal-dev` are absent from Ubuntu 24.04 and Debian 13 (trixie),
and adding the UbuntuGIS PPA on arm64 changed neither GDAL nor PDAL availability
(not investigated further). Ubuntu 22.04 still ships PDAL 2.3 with GDAL 3.4,
too old for Block 3.

- **Base image:** `debian:trixie`, which ships GDAL 3.10 from the official
  repositories. The Ubuntu 24.04 base proposed in the handoff (GDAL 3.8) is
  dropped.
- **PDAL:** deferred to Sprint 9 (GIS Processing), the first sprint that
  processes LiDAR. Sprint 1 installs and proves GDAL only.
- **The system-level decision stands.** When PDAL is added, the preferred route
  is to build a pinned release from source in a builder stage of the same image,
  against the system GDAL, with the source checksum verified. conda/pixi stays
  rejected.

## Amendment 2026-10-15 · PDAL Conditional on ADR-004

The deferral above scheduled PDAL for Sprint 9.
[ADR-007](adr-007-mvp-1-0-scope.md) makes it conditional instead.

- **Whether PDAL is needed at all is decided by ADR-004**, written from the
  feasibility experiment. If height information can be derived from raster
  elevation products, GDAL covers it and PDAL is not required. If point-level
  features are needed, a pure-Python reader installed as a wheel is tried
  first, since it adds no system-level dependency.
- **The system-level route remains the fallback**, unchanged.
- **Nothing blocks on this.** If no route is available without new system
  dependencies, the height-derived indicator group is recorded as unavailable
  and the pipeline continues.

## Alternatives Considered

**Poetry.** Mature and widely known, but slower, and its dependency groups and
lockfile are tool-specific rather than PEP 735. It manages neither the Python
interpreter nor tool runs. Rejected.

**pixi / conda-forge.** Ships GDAL, PDAL and Rasterio as consistent binaries
without touching the system, which solves the bundled-GDAL problem outright.
Rejected because it contradicts the decision to install GDAL/PDAL at system
level, splits the ecosystem between conda and PyPI packages, and adds a second
lock format. Worth revisiting if the Block 3 decision on bindings proves
painful.

**pip + pip-tools with venv.** Minimal, but three tools to do what uv does,
with no interpreter management. Rejected.

**Keep Black alongside Ruff.** Matches the original stack, but duplicates
formatting for no gain. Rejected.

## Consequences

**Positive.** One manifest and one lockfile; host and container resolve the same
versions. The gate is one command that any agent or CI job runs identically,
and pre-commit cannot drift from it. One tool fewer in the gate.

**Negative.** uv is younger than Poetry and pip, and the user must install it on
the host. Pinning bindings to system libraries means a GDAL upgrade is a
deliberate change of the image and the lockfile together. GIS-dependent code
cannot be tested on the host without a matching local GDAL; such tests run in
the container.

**Follow-ups outside the orchestrator's scope** (protected paths, changed by the
user):

- `AGENTS.md` → Code Quality and `.agents/roles/developer.md` → Quality: replace
  "Black" with "Ruff format" and add import-linter.
- `.agents/TOOLING.md` → developer launch command: replace the individual tool
  entries with `Bash(uv run *)`; add `Bash(uv sync*)` where a handoff needs it.
- `.agents/policy.yaml` → developer scope: add `uv.lock` and `.python-version`,
  and `tests/acceptance/.gitkeep` so the developer can create the empty
  directory (`src/**`, including `py.typed`, is already covered).
- `.claude/settings.json` → sandbox network allowlist: `pypi.org`,
  `files.pythonhosted.org`, and the host uv uses to download Python builds.

## Related

- [ADR-003](adr-003-src-layout-and-layer-boundaries.md) — layout and layer
  boundaries
- [Stack](../stack.md), [Architecture](../architecture.md)
- [Sprint 01 log](../../sprints/sprint-01-foundations.md)
