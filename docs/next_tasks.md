# Next Tasks

> The active slice of the plan. The full block and sprint structure lives in
> [roadmap.md](roadmap.md), which is the operational source of truth.
> Updated at the end of every sprint.

The executed subset of the plan is MVP 1.0
([ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)); the per-sprint status
table is in [roadmap.md](roadmap.md).

## Active Sprint

- [ ] **Sprint 3 · CI/CD** (Block 1) — the ADR-005 gate runs on GitHub
  Actions for every push and every pull request to `main`, through the same
  `.pre-commit-config.yaml` the commit hook uses, so the gate keeps one
  definition. Reduced by [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)
  to one workflow running the gate; the image build and CD stay out
  (amendment 2026-10-21). Logged in
  [sprint-03-cicd.md](sprints/sprint-03-cicd.md): handoff
  [009](prompts/009-ci-quality-gate-workflow.md) ACCEPTED 2026-10-21, run
  interactively because `.github/workflows/**` is protected. The sprint stays
  open until the first green run on GitHub.

Running in parallel, since it touches no code:

- [ ] **Feasibility experiment → ADR-004** — measure what the data supports for
  one bounding box: PNOA resolution and available years, which elevation
  products exist for the extent and in what form, and a manually located set of
  candidate sites to reuse as a validation reference. Record it in
  `docs/experiments/exp-001-*.md`; ADR-004 follows from it. Required before
  Sprint 8, and it also decides the elevation route (Sprint 9), the detection
  strategy (Sprints 11–12) and whether the fine-tuning arm of Sprint 18 is
  viable. Methodology fixed in
  [exp-001-data-feasibility.md](experiments/exp-001-data-feasibility.md);
  measurement pending, and it is manual work by the user and the orchestrator,
  not a handoff.

Completed sprints of Block 1: Sprint 1 · Foundations and Quality Gate
(2026-10-14, [log](sprints/sprint-01-foundations.md)) and Sprint 2 · Runtime
Foundations (2026-10-21, [log](sprints/sprint-02-runtime-foundations.md),
handoffs 007 and 008 ACCEPTED). Block 1 closes when Sprint 3 does.

## Blocked On

- [ ] **The bounding box to study** — the feasibility experiment cannot start
  without it. Needed from the user as coordinates or a named extent.

Sprint 3 needs the user to restore the `.github/**` deny entry, commit the diff
and push the branch, so the first run executes on GitHub. That is the user's
action, not a blocker on the agents' side.

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

- [ ] **Block 2 · MLOps and Data Infrastructure** — Sprints 4–6: MLflow, DVC,
  reproducibility. In MVP 1.0 only Sprint 4 runs, reduced to a local file
  store; DVC is deferred and Sprint 6 is absorbed into Sprint 2.

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
- [ ] **CI-PIN · GitHub Actions pinned by tag, not by commit SHA** — the same
  tradeoff the container images already carry. A tag can be moved by its owner.
  Revisit together with digest-pinning the base image.
- [ ] **TOOL-VERIF · `.agents/TOOLING.md` → Pending Verification is stale** —
  `dontAsk` in headless runs has now been exercised by handoffs 007 and 008,
  and the uv cache question was settled by `[tool.uv] cache-dir = ".uv-cache"`
  in `pyproject.toml` (commit `dc769b9`). The file is protected, so the user
  updates it.
- [ ] **W2 · Secret pattern drift** — the guard must validate the full `.env.*`
  glob; the tool deny list enumerates variants one by one and can fall behind.
- [ ] **W3 · Permission coverage** — verify empirically whether `Edit(...)` deny
  rules also cover file writes, and record the result in `.agents/TOOLING.md`.
- [ ] **W12 · Redundant rule** — the `--no-verify` deny entry is covered by the
  broader commit deny; remove it.

## Backlog

- [ ] Research state-of-the-art for abandoned infrastructure detection (Sprint 11;
  in MVP 1.0, to the depth the ADR-004 strategy decision needs).
- [ ] Evaluate PNOA/LiDAR data sources and download APIs (Sprint 8; first pass in
  the feasibility experiment above).
- [ ] Define abandonment indicators taxonomy (Sprint 14).

## Last Updated

2026-10-21
