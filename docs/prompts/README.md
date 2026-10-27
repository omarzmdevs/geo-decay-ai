# Handoffs

> A handoff is the written specification that moves work from the orchestrator to
> an implementing role. It is the unit of traceability in this project: what was
> asked, what was delivered, what ran and whether it was accepted.
>
> Format and required fields: `AGENTS.md` → Handoffs. Template:
> [_template.md](_template.md).

## Naming

`NNN-short-title.md`, numbered sequentially from `001`, never renumbered.

## Index

<!-- Add one line per handoff, newest last -->
<!-- e.g. - [001 · Base pyproject](001-base-pyproject.md) — Sprint 1 — ACCEPTED -->

- [001 · Project skeleton and quality gate](001-project-skeleton-and-gate.md) — Sprint 1 — ACCEPTED
- [002 · Container image and DevContainer](002-container-and-devcontainer.md) — Sprint 1 — ACCEPTED 2026-10-14, together with 006
- [003 · Write-scope policy guard](003-policy-guard.md) — Sprint 1 — ACCEPTED 2026-10-12, experimental run (criteria 1, 2 and 5 not verifiable)
- [004 · Pre-commit quality gate](004-pre-commit-gate.md) — Sprint 1 — ACCEPTED 2026-10-12
- [005 · Restrict Ruff to Python files](005-ruff-python-only.md) — Sprint 1 — ACCEPTED
- [006 · Container image with GDAL only](006-container-gdal-only.md) — Sprint 1 — ACCEPTED 2026-10-14
- [007 · Bounding box and centralised configuration](007-bounding-box-and-configuration.md) — Sprint 2 — ACCEPTED 2026-10-16
- [008 · Logging configuration](008-logging-configuration.md) — Sprint 2 — ACCEPTED 2026-10-17
- [009 · CI quality-gate workflow](009-ci-quality-gate-workflow.md) — Sprint 3 — ACCEPTED 2026-10-21; sprint closed 2026-10-25 on the first green run
- [010 · Experiment-tracking port and configuration](010-experiment-tracking-port-and-config.md) — Sprint 4 — PENDING
- [011 · MLflow adapter, null adapter and the import contract](011-mlflow-adapter-and-import-contract.md) — Sprint 4 — PENDING
- [012 · Tracking composition root and the first CLI command](012-tracking-composition-and-cli.md) — Sprint 4 — PENDING

## Lifecycle

1. The orchestrator writes the handoff; the user commits every handoff of a
   sprint together, so they are frozen before anything runs.
2. The implementing role executes it, leaving the work in the working tree.
3. Whoever launched the task fills `## Run Record`.
4. The orchestrator verifies independently and fills `## Verification`.
5. The documenter records the verdict; the user commits the combined diff.

A handoff without acceptance criteria and a verification command must not be
executed autonomously.
