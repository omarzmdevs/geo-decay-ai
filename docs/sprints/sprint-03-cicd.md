# Sprint 03 · CI/CD

## Block

Block 1 · Architecture and Infrastructure

## Goal

Every push to the repository is validated by the same quality gate that runs
locally, so a broken commit is visible on GitHub and not only on the machine
that made it.

## Execution Mode

**Interactive, with the user's explicit approval.** The deliverable lives in
`.github/workflows/`, which `.agents/policy.yaml` lists as protected: no
headless run may create or change it. The user lifts the deny entry for that
session, as in handoffs 002, 004 and 006, and restores it afterwards.

## Requirements

* One workflow, `.github/workflows/quality-gate.yml`, running the ADR-005 gate
  on GitHub Actions: Ruff (lint and format), strict MyPy, import-linter and
  Pytest.
* The gate has **one definition**. CI runs it through
  `uv run pre-commit run --all-files`, the same hook file the commit hook uses,
  so CI and the local hook cannot drift apart.
* `uv sync --frozen`, so a lockfile that no longer matches `pyproject.toml`
  fails the run instead of being silently relocked.
* Least privilege and bounded cost: `permissions: contents: read`, a job
  timeout, and in-progress runs cancelled when a branch is pushed again.
* Every `uses:` pinned to a release tag, never to a branch.
* No secret is read by the workflow, and none is needed: the gate touches no
  network service.

## Prerequisites

* [ADR-005](../architecture/adr/adr-005-dependency-and-environment-manager.md) —
  the gate and the rule that every tool runs through `uv run`.
* [ADR-007](../architecture/adr/adr-007-mvp-1-0-scope.md) — reduces this sprint
  to one workflow running the gate; amended 2026-10-21 with what that excludes.
* Sprint 1, handoff [004](../prompts/004-pre-commit-gate.md) —
  `.pre-commit-config.yaml`, the gate definition CI reuses.
* A GitHub remote: `origin` → `github.com/omarzmdevs/geo-decay-ai`.
* The user lifting the `.github/**` deny entry for the execution session.

## Tasks

- [x] [009](../prompts/009-ci-quality-gate-workflow.md) — `quality-gate.yml`.
      Interactive, protected path.
- [x] Orchestrator: verify 009 against its criteria, re-run the local gate,
      append the `## Verification` section; then run the documenter.
- [x] User: review and commit the diff, restore the deny entry, and push the
      branch so the first run executes on GitHub. Run #2 executed on `bloque-1`
      at `d061937`; the deny entry `Edit(./.github/workflows/**)` is back in
      the tool settings, checked by the orchestrator on 2026-10-25.
- [x] User: report the run's result — a green run on GitHub is what closes the
      sprint, since no local check can prove the workflow runs. Recorded in
      handoff 009's `## Sprint Closing Evidence`: run #2, `success`.
- [x] Orchestrator: add the status badge to `README.md` once a run is green.
      Added 2026-10-25, after run #2.
- [ ] User, optional: require the check on `main` in the repository's branch
      protection. Outside the repository, so it is the user's action and is
      recorded here, not automated.
- [x] Sprint close: fill the dates and the verdict here, update
      `current_state.md` and `next_tasks.md`, and move the sprint to complete
      in the directory index.

## Deliverable

A push to any branch, and any pull request to `main`, runs the full gate on
GitHub Actions and reports pass or fail on the commit.

## Verdict

Complete, 2026-10-25. The closing criterion is met: the first green run of
`Quality gate` on GitHub — run #2, branch `bloque-1`, commit `d061937`,
conclusion `success` (2026-10-24T23:04:48Z). Source: handoff
[009](../prompts/009-ci-quality-gate-workflow.md), `## Sprint Closing Evidence`,
read by the orchestrator from the GitHub Actions API.

## Handoffs Executed

- [009 · CI quality-gate workflow](../prompts/009-ci-quality-gate-workflow.md) — ACCEPTED 2026-10-21 (orchestrator verification). Run by an in-process developer subagent (`haiku`, planned tier `TIER_LIGHT`) from restore point `d40898d`, outcome completed. Gate: `workflow ok` and all six pre-commit hooks passing on the tree as delivered. Sprint closed 2026-10-25 on the first green run on GitHub (see Verdict).

## Notes

- **The Docker image build stays out of CI**, which is what ADR-007's "one
  workflow running the gate" reduces this sprint to; the roadmap's original
  scope line, which named the image build, is amended accordingly. The image is
  built and used daily by the DevContainer, so a CI build would spend several
  minutes compiling a GDAL image to repeat a signal the developer already has.
  Nothing is deleted from the plan: the build enters CI the moment the
  container stops being built daily, or as a workflow triggered only by changes
  to `Dockerfile`, `docker-compose.yml`, `.devcontainer/**`, `pyproject.toml`
  and `uv.lock`. Tracked as **CI-IMAGE** in `next_tasks.md`.
- **CI runs the gate through pre-commit rather than listing the five commands
  again.** Two lists drift; one does not. The cost is that CI depends on the
  hook file, which is the intended coupling: `.pre-commit-config.yaml` is the
  gate.
- **Actions are pinned by tag, not by commit SHA**, which is the same tradeoff
  the container images already carry (`debian:trixie`). A tag can be moved by
  its owner, so this is a supply-chain weakness, recorded as **CI-PIN** in
  `next_tasks.md` rather than left implicit.
- **CD is not in this sprint and not in MVP 1.0.** There is nothing to deploy
  until Sprints 20 and 21, and ADR-007 defers the platform work. The sprint
  keeps the roadmap's "CI/CD" title for traceability; its executed scope is CI.

- **Deviation: run #1 failed.** Run #1 (`410f96f`) failed because the SHA pin of
  `actions/checkout` was malformed (a stray `v` before the digest), so the ref
  did not resolve. Fixed in `d061937`, which also pins `astral-sh/setup-uv` by
  digest. Source: handoff 009, `## Sprint Closing Evidence`.
- **Open after close:** whether the uv cache is restored can only be read from a
  run's log (handoff 009, Verification notes); the status badge and the optional
  branch-protection check above stay open. Debt `CI-PIN` now applies to digests
  kept in step with their version comments.

## Documents Updated

<!-- Completed as the sprint runs. -->

- [README.md](../../README.md) — `Quality gate` status badge (2026-10-25)
- [docs/sprints/README.md](README.md) — directory index: Sprint 3 marked complete (2026-10-25)
- [docs/current_state.md](../current_state.md) — Active Sprint, Completed Sprints and Current Milestone: Sprint 3 complete, Block 1 closed (2026-10-25)
- [docs/next_tasks.md](../next_tasks.md) — Active Sprint, Completed Sprints of Block 1 and Blocked On: Sprint 3 closed (2026-10-25)

## Date Started

2026-10-21

## Date Completed

2026-10-25
