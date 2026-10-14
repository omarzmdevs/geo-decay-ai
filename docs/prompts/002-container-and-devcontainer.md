# Handoff 002 · Container Image and DevContainer

## Objective

A reproducible container, the reference environment of ADR-005, has GDAL and
PDAL at system level and passes the full quality gate on the handoff-001
skeleton.

## Role

developer

## Tier

`TIER_STANDARD` — infrastructure configuration with known components; no GIS
code.

## Files to Read

- `docs/architecture/adr/adr-005-dependency-and-environment-manager.md`
- `pyproject.toml`, `.python-version`

## Files to Create or Modify

- `Dockerfile` *(protected)*
- `docker-compose.yml` *(protected)*
- `.devcontainer/devcontainer.json` *(protected)*
- `.dockerignore`

## Out of Scope

- Python GIS bindings (`gdal`, `rasterio`, `pdal`, ...). ADR-005 defers them to
  Block 3. This sprint only proves that the system libraries load.
- PostGIS, MLflow and any other service. Compose has a single `app` service.
- `pyproject.toml` and `uv.lock`. If they need a change, stop and report it.
- CI workflows (Sprint 3).

## Acceptance Tests

no — infrastructure.

## Execution Mode

**Interactive only**, with the user's explicit approval for each protected file
(`AGENTS.md` → Security Rules 3 and 7). Never headless.

## Specification

- The base image is pinned to an explicit version tag, never `latest`. It must
  provide GDAL and PDAL command-line tools and libraries at system level.
  Example: Ubuntu 24.04 LTS with `gdal-bin`/`libgdal-dev` and `pdal`, or an
  OSGeo GDAL image with PDAL added. Record the chosen versions in the report.
- uv is copied from `ghcr.io/astral-sh/uv:<pinned version>`. uv installs
  Python 3.12 from `.python-version`.
- The project virtualenv lives outside the bind-mounted repository (e.g.
  `UV_PROJECT_ENVIRONMENT=/opt/venv`), so the host's macOS `.venv` is never used
  in the container and the container never overwrites it.
- Dependencies install with `uv sync --locked`, as a cached layer that runs
  before the source is copied.
- The container runs as a non-root user.
- `.dockerignore` excludes `.git`, `.venv`, caches, heavy data
  (`data/`, `models/`, `*.tif`, `*.laz`, ...) and every secret pattern of
  `.agents/policy.yaml` (`.env`, `.env.*`, `*.pem`, `*.key`, `credentials.json`),
  with `!.env.example`.
- `devcontainer.json` uses the compose `app` service, contains no comments (so
  it parses as plain JSON), and installs no editor-specific extensions.

## Acceptance Criteria

1. `docker compose build` succeeds.
2. `gdalinfo --version` and `pdal --version` run inside the container.
3. The container interpreter is Python 3.12, and the user id is not 0.
4. The full ADR-005 gate passes inside the container.
5. `.dockerignore` covers every secret pattern, and its only exception is `.env.example`.
6. No `FROM` line uses `latest`. The script checks this; whether every
   external image has an explicit tag is checked in review, because stage
   aliases (`FROM base AS dev`) carry no tag.
7. `.devcontainer/devcontainer.json` is valid JSON.
8. `git status --short` shows only the files listed above.

## Verification Command

```bash
docker compose build \
  && docker compose run --rm app gdalinfo --version \
  && docker compose run --rm app pdal --version \
  && docker compose run --rm app sh -c 'test "$(id -u)" != 0' \
  && docker compose run --rm app uv run python -c 'import sys; assert sys.version_info[:2] == (3, 12)' \
  && docker compose run --rm app sh -c 'uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest' \
  && for p in '.env' '.env.*' '*.pem' '*.key' 'credentials.json' '!.env.example'; do grep -qxF -- "$p" .dockerignore || exit 1; done \
  && ! grep -Eiq '^FROM +[^ ]+:latest' Dockerfile \
  && python3 -m json.tool .devcontainer/devcontainer.json > /dev/null \
  && git status --short
```

## Launch Command

Interactive session only, started with `ROLE: developer`, with the
infrastructure deny entries lifted for that session as `.agents/TOOLING.md`
describes. First message:
`ROLE: developer. Execute docs/prompts/002-container-and-devcontainer.md`

## Restore Point

<!-- Filled by whoever launches: `git rev-parse HEAD` right before launch -->

e5f4877

---

## Run Record

Date: 2026-10-14
Tool and model: Claude Code, in-process developer subagent (`sonnet`, matching
`TIER_STANDARD`) launched from the interactive orchestrator session, with the
Docker deny entries lifted by the user. The agent ran no Docker command; the
user ran the Docker steps.
Outcome: failed at criterion 1 — `pdal` and `libpdal-dev` do not exist in
Ubuntu 24.04. Completed through handoff 006.

## Verification

Verdict: ACCEPTED together with handoff 006 (criterion 2 superseded: GDAL only,
PDAL deferred to Sprint 9 by the ADR-005 amendment of 2026-10-14)
Files changed: `Dockerfile`, `docker-compose.yml`,
`.devcontainer/devcontainer.json`, `.dockerignore`.
Gate: user-run Docker on macOS arm64 (`docker-verify.log`, EXIT=0):
`docker compose build` succeeds; `GDAL 3.10.3, released 2025/04/01`; `id -u` = 1000;
Python 3.12.15; inside the container ruff check, ruff format --check, mypy
(10 files), lint-imports (4 kept) and pytest (76 passed) all pass. Static checks
(`.dockerignore` patterns, no `:latest`, valid devcontainer JSON, git status)
re-run by the orchestrator: pass.
Notes:
- Orchestrator review before the build: `.dockerignore` excluded secrets only at
  the root (`sub/.env.prod` would have entered the image) and the runtime cache
  directories could be root-owned. Both fixed by the developer (`**/.env*`,
  user-owned `~/.cache/{uv,mypy,ruff}`).
- External images pinned by tag, not digest; apt packages unpinned. Accepted for
  now; builds are not bit-reproducible.
- Each `uv run` re-installs the editable project (~1 s) because the bind-mounted
  source differs from the copy built into the image. Harmless; can be avoided
  later with `UV_NO_SYNC=1` in the container if it becomes a nuisance.
