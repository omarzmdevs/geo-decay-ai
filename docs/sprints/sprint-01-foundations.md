# Sprint 01 · Foundations and Quality Gate

## Block

Block 1 · Architecture and Infrastructure

## Goal

Create the professional project structure and the automated quality gate that
every later sprint depends on. No business logic.

## Execution Mode

**Interactive, with explicit user approval.** Most deliverables are protected
paths (`Dockerfile*`, `docker-compose*.yml`, `.devcontainer/`,
`.pre-commit-config.yaml`), which `.agents/policy.yaml` forbids changing in a
headless run.

## Requirements

* Standard project structure: `src/`, `tests/unit/`, `tests/acceptance/`, `scripts/`.
* Python environment and dependency management defined in `pyproject.toml`.
* Docker, Docker Compose and DevContainer with GDAL, PDAL and Rasterio installed
  at system level.
* Quality gate: Ruff, Black, strict MyPy, Pytest, pre-commit.
* Write-scope guard enforcing `.agents/policy.yaml` on the working-tree diff.

## Prerequisites

* ADR-003 — `src/` layout and layer boundaries.
* ADR-005 — dependency and environment manager.

Both must be recorded before implementation starts: the orchestrator owns
system-level architecture, so the developer must not invent the layout.

## Tasks

- [ ] Define the base `pyproject.toml`, including the dev dependencies and the
      tool configuration for Ruff, Black, MyPy and Pytest.
- [ ] Create `Dockerfile` / `docker-compose.yml` and the DevContainer, ensuring
      GDAL and PDAL are installed at system level.
- [ ] Create the directory structure: `src/`, `tests/unit/`, `tests/acceptance/`,
      `scripts/`.
- [ ] Configure `.pre-commit-config.yaml` with the full gate.
- [ ] Implement `scripts/policy_guard.py` with unit tests: it reads
      `.agents/policy.yaml`, takes `--role <role>`, and fails when the changed
      files touch a secret, a protected path, or a path outside that role's
      scope. Wire it as a hook.
- [ ] Add `scripts/policy_guard.py` to the tool deny list once validated, so no
      agent can modify its own guard.
- [ ] Verify the agent environment inside the container: the most restrictive
      headless permission mode behaves as documented, and the sandbox is
      compatible with Docker and with package installation (see
      `.agents/TOOLING.md` → Pending Verification).

## Deliverable

A project that runs with no business logic, whose quality gate runs
automatically, and whose write scopes are enforced rather than merely documented.

## Handoffs Executed

<!-- List the handoffs run during this sprint -->

## Notes

<!-- Any relevant observations, issues encountered, or deviations from the plan -->

## Documents Updated

- [docs/current_state.md](../current_state.md)
- [docs/next_tasks.md](../next_tasks.md)

## Date Started

<!-- YYYY-MM-DD -->

## Date Completed

<!-- YYYY-MM-DD -->
