# Handoff 006 · Container on Debian Trixie with GDAL Only

## Objective

The handoff-002 container builds on `debian:trixie` with GDAL at system level
and no PDAL, and passes the full quality gate, as the ADR-005 amendment of
2026-10-14 decides.

## Role

developer

## Tier

`TIER_STANDARD` — a small, targeted change to an existing Dockerfile; no GIS code.

## Context

Handoff 002 failed at `docker compose build`: `pdal` and `libpdal-dev` do not
exist in Ubuntu 24.04. This handoff amends the uncommitted 002 work in the
working tree. **It supersedes criterion 2 of handoff 002**: PDAL is no longer
required in Sprint 1. 002 and 006 are verified and committed together.

## Files to Read

- `docs/architecture/adr/adr-005-dependency-and-environment-manager.md` →
  Amendment 2026-10-14
- `Dockerfile`, `docker-compose.yml`, `.devcontainer/devcontainer.json`,
  `.dockerignore` (from handoff 002, uncommitted)

## Files to Create or Modify

- `Dockerfile` *(protected)*

## Out of Scope

- PDAL in any form (system package, source build, conda). It is Sprint 9.
- `docker-compose.yml`, `.devcontainer/devcontainer.json`, `.dockerignore`,
  unless the base image change breaks them; if so, stop and report.
- `pyproject.toml`, `uv.lock`, `.python-version`.
- Running any `docker` command: the user runs the Docker steps.

## Acceptance Tests

no — infrastructure.

## Execution Mode

**Interactive only**, with the user's explicit approval for the protected file.

## Specification

- Base image `debian:trixie`, pinned by tag (never `latest`).
- System packages: `gdal-bin` and `libgdal-dev` (GDAL 3.10), plus
  `ca-certificates` and `git` as before. Remove `pdal` and `libpdal-dev`.
- Debian has no default `ubuntu` user: the user-creation step must still work
  (UID/GID 1000 free) without relying on removing one.
- Everything else from handoff 002 is kept: uv pinned image, `/opt/venv`,
  `/opt/python`, cache directories owned by the user, two-layer `uv sync
  --locked`, non-root user, `CMD ["bash"]`.
- Update comments that mention Ubuntu or PDAL.

## Acceptance Criteria

1. `docker compose build` succeeds. *(user)*
2. `gdalinfo --version` reports GDAL 3.10.x inside the container. *(user)*
3. The container interpreter is Python 3.12, and the user id is not 0. *(user)*
4. The full ADR-005 gate passes inside the container. *(user)*
5. Handoff 002 criteria 5–8 still hold.
6. `grep -Ei 'pdal' Dockerfile` finds no package install line.

## Verification Command

Static part (developer and orchestrator):

```bash
for p in '.env' '.env.*' '*.pem' '*.key' 'credentials.json' '!.env.example'; do grep -qxF -- "$p" .dockerignore || exit 1; done \
  && ! grep -Eiq '^FROM +[^ ]+:latest' Dockerfile \
  && grep -Eq '^FROM +debian:trixie' Dockerfile \
  && ! grep -Eq '^\s+(lib)?pdal' Dockerfile \
  && python3 -m json.tool .devcontainer/devcontainer.json > /dev/null \
  && git status --short
```

Docker part (user):

```bash
docker compose build \
  && docker compose run --rm app gdalinfo --version \
  && docker compose run --rm app sh -c 'test "$(id -u)" != 0' \
  && docker compose run --rm app uv run python -c 'import sys; assert sys.version_info[:2] == (3, 12)' \
  && docker compose run --rm app sh -c 'uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest'
```

## Launch Command

Interactive session only, started with `ROLE: developer`, with the Docker deny
entries lifted for that session. First message:
`ROLE: developer. Execute docs/prompts/006-container-gdal-only.md`

## Restore Point

<!-- Filled by whoever launches: `git rev-parse HEAD` right before launch -->

---

## Run Record

Date:
Tool and model:
Outcome:

## Verification

Verdict:
Files changed:
Gate:
Notes:
