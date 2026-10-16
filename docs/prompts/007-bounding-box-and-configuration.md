# Handoff 007 · Bounding Box and Centralised Configuration

## Objective

The project reads every runtime setting from one validated, typed
configuration object, including the target bounding box, and fails at start-up
with a clear message when that configuration is wrong.

## Role

developer — preceded by a developer session in **tester mode** (see Acceptance
Tests).

## Tier

`TIER_STANDARD` — ordinary typed Python and validation logic; no GIS
computation, no model code.

## Context

Sprint 2, first of two handoffs. This one establishes configuration; handoff
008 configures logging on top of it, so this must land first.

The bounding box is the system's unit of work. It is held as a configuration
variable so the covered extent is selected without touching code, and the same
value is later filled by the CLI, by the API and by the map selection of
Sprint 21. Its correctness is a data contract: a swapped axis order or an
unchecked extent produces results that look plausible and are wrong, which is
why this handoff carries acceptance tests.

## Files to Read

- `docs/architecture/adr/adr-003-src-layout-and-layer-boundaries.md`
- `docs/architecture/adr/adr-006-logging-strategy.md` → Decision (only to see
  where configuration is consumed; logging itself is handoff 008)
- `pyproject.toml`
- `src/geo_decay_domain/__init__.py`, `src/geo_decay_delivery/__init__.py`

## Files to Create or Modify

- `src/geo_decay_domain/bounding_box.py` — the value object
- `src/geo_decay_delivery/config.py` — the settings object
- `tests/unit/domain/test_bounding_box.py`
- `tests/unit/delivery/test_config.py`
- `.env.example`
- `pyproject.toml`, `uv.lock` — one runtime dependency added

## Out of Scope

- Logging configuration in any form. That is handoff 008.
- Applying `GEO_DECAY_RANDOM_SEED` anywhere — seeding `random`, `numpy` or any
  framework. The variable is declared, not consumed.
- Any CLI or API entry point. Sprints 20 and 21.
- Reprojection between coordinate reference systems. The bounding box carries
  its CRS as data; converting between CRSs is Sprint 9 and is decided by
  ADR-004.
- Choosing the project's working CRS. ADR-004 decides it; this handoff must
  not hard-code one as a default.
- `tests/acceptance/**` — written in tester mode, before this session, and not
  touched by the implementing session.

## Specification

**`BoundingBox`, in the domain.** A frozen dataclass with `min_x`, `min_y`,
`max_x`, `max_y` as floats and `crs` as a string. Pure standard library: the
domain-purity contract forbids heavy libraries there, and the settings
framework must not reach into it either.

- Axis order is **x first, then y** — longitude/easting before
  latitude/northing — documented in the docstring. This is the single most
  common silent error in geospatial code and the reason this object exists.
- `min_x < max_x` and `min_y < max_y`, both strict: a degenerate box is an
  error, not an empty result.
- `crs` is required and non-empty, normalised to upper case, and must match
  the authority form `AUTHORITY:CODE` (for example `EPSG:4326`).
- When `crs` is `EPSG:4326`, longitudes are within `[-180, 180]` and latitudes
  within `[-90, 90]`. For any other authority code no range check is applied,
  because the valid range depends on the projection.
- Invalid input raises `ValueError` with a message naming the offending field
  and the value received.

**`Settings`, in delivery.** Built with `pydantic-settings`, reading from the
environment with the prefix `GEO_DECAY_`, and from `.env` when present.

- `GEO_DECAY_BBOX` — four comma-separated numbers in `min_x,min_y,max_x,max_y`
  order, parsed into a `BoundingBox`.
- `GEO_DECAY_BBOX_CRS` — the authority code the four numbers are expressed in.
- `GEO_DECAY_LOG_LEVEL` and `GEO_DECAY_LOG_FORMAT` — declared here with
  defaults so handoff 008 can consume them; this handoff does not act on them.
- `GEO_DECAY_DATA_DIR` — base directory for data written by later sprints,
  defaulting to `data/`.
- `GEO_DECAY_RANDOM_SEED` — the project-wide deterministic seed, an integer with
  a default. Declared here only: Sprint 6 is absorbed into this sprint
  (ADR-007), and externalising the seed is the part of it that belongs to
  configuration. Nothing in the project is random yet, so no code applies it;
  the sprint that first trains or samples does.
- A validation failure raises at construction, and the message says which
  variable is wrong. Settings are constructed explicitly by the caller and
  passed down; no module-level singleton and no import-time environment read.

**Dependency.** Add `pydantic-settings` to `[project].dependencies` and update
the lockfile. Rationale, for the report: the Sprint 2 deliverable is
configuration *validated at start-up*, and hand-rolling parsing, type coercion,
`.env` loading and error messages is more code to own than the dependency.
It is confined to the delivery layer, so no other layer depends on it.

**`.env.example`.** Every variable above, with placeholder values and a
one-line comment each. No real coordinates, no secrets.

## Acceptance Tests

**yes** — the bounding box is a data contract and the axis-order and extent
rules are exactly the kind of error that stays silent.

A developer session in tester mode writes `tests/acceptance/test_bounding_box_contract.py`
**before** this handoff is implemented, covering: axis order is x-then-y;
`min >= max` rejected on both axes; missing or malformed CRS rejected;
out-of-range values rejected for `EPSG:4326` and not range-checked for a
projected CRS; the object is immutable. The user commits those failing tests,
and that commit is what proves they were red.

## Acceptance Criteria

1. `tests/acceptance/test_bounding_box_contract.py` passes, unchanged from the
   tester-mode commit.
2. `BoundingBox` is importable from `geo_decay_domain.bounding_box`, is frozen,
   and raises `ValueError` for each invalid case in the Specification.
3. `geo_decay_domain` imports nothing outside the standard library.
4. `Settings` constructed with a valid `GEO_DECAY_BBOX` and `GEO_DECAY_BBOX_CRS`
   exposes a `BoundingBox`; constructed with a malformed one, it raises and the
   message names the variable.
5. No module reads `os.environ` at import time.
6. `.env.example` declares every variable in the Specification and contains no
   real coordinate values.
7. The full ADR-005 gate passes.

## Verification Command

```bash
uv run pytest tests/acceptance/test_bounding_box_contract.py -q \
  && uv run python -c "
import dataclasses, sys
from geo_decay_domain.bounding_box import BoundingBox
assert dataclasses.is_dataclass(BoundingBox) and BoundingBox.__dataclass_params__.frozen
for bad in [(1,1,0,2,'EPSG:4326'), (0,1,2,1,'EPSG:4326'), (0,0,1,1,''), (0,0,1,1,'4326'), (-181,0,1,1,'EPSG:4326')]:
    try: BoundingBox(*bad); sys.exit('accepted invalid: %r' % (bad,))
    except ValueError: pass
BoundingBox(-3.7, 40.4, -3.6, 40.5, 'EPSG:4326')
" \
  && ! grep -rEq '^[^#]*os\.environ' src/geo_decay_domain src/geo_decay_data src/geo_decay_application \
  && for v in GEO_DECAY_BBOX GEO_DECAY_BBOX_CRS GEO_DECAY_LOG_LEVEL GEO_DECAY_LOG_FORMAT GEO_DECAY_DATA_DIR GEO_DECAY_RANDOM_SEED; do grep -q "^$v=" .env.example || exit 1; done \
  && uv run python -c "
import subprocess, sys
r = subprocess.run([sys.executable, '-c', 'from geo_decay_delivery.config import Settings; Settings()'],
                   env={'PATH': '/usr/bin:/bin', 'GEO_DECAY_BBOX': '1,2,3', 'GEO_DECAY_BBOX_CRS': 'EPSG:4326'},
                   capture_output=True, text=True)
assert r.returncode != 0 and 'BBOX' in (r.stderr + r.stdout).upper(), r.stderr
" \
  && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest \
  && git status --short
```

## Launch Command

Tester mode, first:

```bash
claude -p "ROLE: developer, tester mode. Execute the acceptance-test part of docs/prompts/007-bounding-box-and-configuration.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

Implementation, after the user has committed the failing tests:

```bash
claude -p "ROLE: developer. Execute docs/prompts/007-bounding-box-and-configuration.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" "Bash(uv sync*)" "Bash(uv lock*)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

`uv sync` and `uv lock` are allowed here only because this handoff adds a
dependency.

## Restore Point

Baseline for the sprint: `52232d4` (MVP 1.0 re-scope).

- **Tester-mode run:** `0a77325` — the commit that landed handoffs 007 and 008.
- **Implementation run:** the commit that lands the failing acceptance tests.

---

## Run Record

### Tester mode

Date: 2026-10-16
Restore point: `0a77325`
Tool and model: `claude -p` headless, `--model sonnet`,
`--permission-mode dontAsk`, with the allowlist in the launch command above.
Two runs: the first wrote the file; the second, same role and allowlist, was
scoped to the lint and format findings of the first and changed nothing else.
Outcome: completed.

Files changed: `tests/acceptance/test_bounding_box_contract.py` only — 257
lines, 23 test functions. The agent could not run the gate itself, so the state
below was established by the orchestrator.

**Red state, verified by the orchestrator on 2026-10-16:**

| Check | Result |
|---|---|
| `uv run pytest tests/acceptance/test_bounding_box_contract.py -q` | **red** — collection error, `ModuleNotFoundError: No module named 'geo_decay_domain.bounding_box'` |
| `uv run ruff check` | All checks passed! |
| `uv run ruff format --check` | 1 file already formatted |
| `uv run mypy` | 3 errors, all in this file |
| `uv run lint-imports` | Contracts: 4 kept, 0 broken |
| `uv run pytest` (full suite) | interrupted by the same collection error |

The red is **by collection, not test by test**, because the module does not
exist yet. It is weaker evidence than 23 individual failures: after the
implementation run, every one of the 23 must pass on its own.

The three mypy errors are `import-not-found` for the missing module and two
`unused-ignore`, at the `# type: ignore[call-arg]` of `test_crs_is_required` and
the `# type: ignore[attr-defined]` of `test_attributes_cannot_be_added`. All
three are artefacts of the absent module: once `BoundingBox` exists, mypy has a
real error to suppress at both sites. If any of them survives the
implementation, the implementation is wrong — the acceptance tests are not
touched to silence it.

### Implementation

Date: 2026-10-16
Restore point: `3757b46`
Tool and model: `claude -p` headless, `--model sonnet`,
`--permission-mode dontAsk`, with the allowlist in the launch command above.
Two runs: the first was interrupted when its session ended, leaving
`bounding_box.py`, `config.py`, `tests/unit/domain/test_bounding_box.py` and
the locked dependency but no `.env.example` entries, no delivery test and a
failing gate. The second, launched by the user from the same handoff with the
remaining items named, finished the task.
Outcome: completed.

Deviation: the second run started from a working tree that already held the
first run's partial work, not from a clean one. The two runs are therefore one
task in the diff, which is what the user reviews.

## Verification

Verdict: **ACCEPTED**

Files changed — exactly the set the handoff lists, and nothing else:

| File | |
|---|---|
| `src/geo_decay_domain/bounding_box.py` | new, 77 lines |
| `src/geo_decay_delivery/config.py` | new, 91 lines |
| `tests/unit/domain/test_bounding_box.py` | new, 31 lines |
| `tests/unit/delivery/test_config.py` | new, 218 lines |
| `.env.example` | six `GEO_DECAY_*` variables appended |
| `pyproject.toml` | `pydantic-settings` declared; `mypy_path = "src"` |
| `uv.lock` | relocked |

`git diff tests/acceptance/` is empty: the acceptance tests are untouched. The
developer reported reverting one blank line `ruff --fix` had added there, and
the empty diff confirms it.

Gate, re-run by the orchestrator: `ruff format --check` 15 files formatted,
`mypy` success on 15 source files, `lint-imports` 4 contracts kept,
`pytest` **167 passed** — the 50 acceptance cases among them. `ruff check`
first reported one `I001` in `tests/acceptance/test_bounding_box_contract.py`,
outside the developer's scope; after the two follow-ups in the Notes the whole
gate is green.

Criteria, checked one by one:

1. Acceptance tests pass unchanged from the tester-mode commit — 50 passed,
   empty diff. ✔
2. `BoundingBox` importable from `geo_decay_domain.bounding_box`, frozen, and
   `ValueError` for every invalid case in the Specification. ✔
3. `geo_decay_domain` imports nothing outside the standard library — `math`,
   `re`, `dataclasses`. ✔
4. `Settings` exposes a `BoundingBox`, and with `GEO_DECAY_BBOX=1,2,3` it
   fails at construction with the variable named. ✔
5. No module reads `os.environ` at import time. ✔
6. `.env.example` declares all six variables with placeholders, no real
   coordinates. ✔
7. The full gate passes. ✔ (After the two follow-ups below; the developer's
   own files were green as delivered.)

Notes:

- **The one ruff finding is not a defect in the delivered work.** Ruff's isort
  heuristic classified `geo_decay_*` as third-party while the packages held
  only `__init__.py`, and as first-party once `bounding_box.py` existed, so the
  import grouping it demanded of the tester in the morning is the opposite of
  what it demands now. Two one-line follow-ups close it: declare
  `[tool.ruff.lint.isort] known-first-party` in `pyproject.toml`, so the
  classification stops depending on what happens to be in the tree, and add the
  blank line ruff asks for in the acceptance file. Both were applied by the user
  on 2026-10-16 and the gate is green. The second touches a frozen
  acceptance test and is authorised here explicitly: it is whitespace inside an
  import block, it changes no assertion, and it is visible as one blank line in
  the diff. Suppressing `I001` for `tests/acceptance/**` was the alternative and
  is worse — it would silence a real rule in the files that matter most, to
  avoid one blank line.
- **`GEO_DECAY_LOG_FORMAT` takes `text` and `json`**, not `console`. Handoff 008
  was written with `console`; ADR-006 names no values. Handoff 008 has been
  amended to `text` rather than asking for a rename here, because the value is
  declared, tested and documented in this handoff's deliverables and the naming
  carries no consequence.
- The first run left `dependencies = []` although `uv.lock` already carried
  `pydantic-settings`. The second run declared it and relocked. Had the task
  stopped at the interruption, the project would have run on a dependency it
  did not declare.
- `GEO_DECAY_RANDOM_SEED` is declared and unused, as specified: the seeding
  function belongs to the first sprint that trains or samples.
