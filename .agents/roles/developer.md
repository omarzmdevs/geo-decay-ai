# Developer Role

> Code, unit tests and the quality gate. Shared rules: `AGENTS.md`.

## Tier

- `TIER_STANDARD` by default.
- `TIER_DEEP` for complex GIS processing, computer vision pipelines, ML models or hard debugging, when the handoff says so.

## Owns

- `src/`, `tests/unit/`, `pyproject.toml`, `scripts/` — exact scope in `.agents/policy.yaml`.
- Module, class and function design inside the sprint boundary.
- Docstrings and code comments.

## Never

- Edit `tests/acceptance/`. If an acceptance test looks wrong, stop and report it.
- Edit project state or planning documents (`docs/current_state.md`, `docs/next_tasks.md`, `docs/sprints/`, `docs/prompts/`, `docs/architecture/`).
- Create new bounded contexts or change system-level architecture — report the need to the orchestrator.

## Implementation Guidelines

1. **Quality**: Black formatting, Ruff linting, strict MyPy typing, Pytest coverage for all logic.
2. **Execution over planning**: no long theoretical plans unless asked; write, test, iterate.
3. **Clean Architecture**: ML/GIS logic decoupled from FastAPI/CLI delivery; SOLID.
4. **Preservation**: keep existing behaviour and passing tests when refactoring.

## Finishing a Task

1. Run the handoff's verification command and the full quality gate.
2. Stage only the files named in the handoff with `git add`. Never commit.
3. End with a short report: proposed commit message, staged files, gate result, deviations from the handoff, open questions.

## Tester Mode

Used only when the handoff says `Acceptance tests: yes`, in a session separate from the implementation.

- Write tests in `tests/acceptance/` from the handoff's acceptance criteria — never from existing code.
- Tests must fail before implementation; confirm and report the failure.
- Do not write or edit anything in `src/`.
- Stage the tests with `git add`; never commit. The user commits them before implementation starts.

## Protected Paths

Infrastructure files (`Dockerfile*`, `docker-compose*.yml`, `.devcontainer/`,
`.pre-commit-config.yaml`, `.github/workflows/`) are protected. Sprints that need
them are done in an interactive session with the user's explicit approval,
never headless.
