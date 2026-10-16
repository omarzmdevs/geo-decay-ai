# Next Tasks

> The active slice of the plan. The full block and sprint structure lives in
> [roadmap.md](roadmap.md), which is the operational source of truth.
> Updated at the end of every sprint.

The executed subset of the plan is MVP 1.0
([ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)); the per-sprint status
table is in [roadmap.md](roadmap.md).

## Active Sprint

- [ ] **Sprint 2 · Runtime Foundations** (Block 1) — logging
  ([ADR-006](architecture/adr/adr-006-logging-strategy.md)), environment
  variables, centralised configuration, including the target bounding box as a
  configuration variable and the deterministic seed absorbed from Sprint 6.
  Planned in [sprint-02-runtime-foundations.md](sprints/sprint-02-runtime-foundations.md):
  handoff [007](prompts/007-bounding-box-and-configuration.md) (bounding box and
  configuration, acceptance tests first) then
  [008](prompts/008-logging-configuration.md) (logging), both headless and
  awaiting the user's commit of the handoffs.

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

Sprint 1 · Foundations and Quality Gate is completed (2026-10-14, see
[sprint-01-foundations.md](sprints/sprint-01-foundations.md)).

## Blocked On

- [ ] **The bounding box to study** — the feasibility experiment cannot start
  without it. Needed from the user as coordinates or a named extent.

Nothing blocks Sprint 2 planning. The per-session lift of the infrastructure deny
entries for handoffs 002 and 004 was done.

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

- [ ] **Sprint 3 · CI/CD** (Block 1) — GitHub Actions: lint, format, type check,
  tests, Docker build. Reduced in MVP 1.0 to one workflow running the gate.
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

2026-10-16
