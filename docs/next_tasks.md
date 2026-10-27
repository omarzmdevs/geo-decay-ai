# Next Tasks

> The active slice of the plan. The full block and sprint structure lives in
> [roadmap.md](roadmap.md), which is the operational source of truth.
> Updated at the end of every sprint.

The executed subset of the plan is MVP 1.0
([ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)); the per-sprint status
table is in [roadmap.md](roadmap.md).

## Active Sprint

- [ ] **Sprint 4 · MLflow** (Block 2) — experiment tracking in place before the
  first experiment exists: a tracking port in the domain, an MLflow adapter
  confined to the data layer, a null adapter, and composition in delivery with
  the store addressed by a configuration string. Reduced by
  [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md) to a local file store;
  the decisions are in
  [ADR-008](architecture/adr/adr-008-experiment-tracking.md). Planned in
  [sprint-04-mlflow.md](sprints/sprint-04-mlflow.md) with handoffs
  [010](prompts/010-experiment-tracking-port-and-config.md),
  [011](prompts/011-mlflow-adapter-and-import-contract.md) and
  [012](prompts/012-tracking-composition-and-cli.md), run in that order, each
  committed separately. Sprint 4 is the only sprint of Block 2 that MVP 1.0
  executes, so the block closes with it.

Closed, kept here until Block 2 records its first verdict:

- [x] **Sprint 3 · CI/CD** (Block 1) — the ADR-005 gate runs on GitHub
  Actions for every push and every pull request to `main`, through the same
  `.pre-commit-config.yaml` the commit hook uses, so the gate keeps one
  definition. Reduced by [ADR-007](architecture/adr/adr-007-mvp-1-0-scope.md)
  to one workflow running the gate; the image build and CD stay out
  (amendment 2026-10-21). Logged in
  [sprint-03-cicd.md](sprints/sprint-03-cicd.md): handoff
  [009](prompts/009-ci-quality-gate-workflow.md) ACCEPTED 2026-10-21, run
  interactively because `.github/workflows/**` is protected. Closed 2026-10-25
  on the first green run on GitHub (run #2, `d061937`, `success`), per the
  handoff's `## Sprint Closing Evidence`.

**Reserved by the user on 2026-10-26**, so it is out of the active slice until
the bounding box exists. Block 2 proceeds without it:

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
(2026-10-14, [log](sprints/sprint-01-foundations.md)), Sprint 2 · Runtime
Foundations (2026-10-21, [log](sprints/sprint-02-runtime-foundations.md),
handoffs 007 and 008 ACCEPTED) and Sprint 3 · CI/CD (2026-10-25,
[log](sprints/sprint-03-cicd.md), handoff 009 ACCEPTED). Block 1 closed 2026-10-25.

## Blocked On

- [ ] **The bounding box to study** — the feasibility experiment cannot start
  without it. Needed from the user as coordinates or a named extent.
  Reserved by the user on 2026-10-26: nothing in Block 2 depends on its value —
  Sprint 4's smoke run supplies a throwaway extent — and it becomes blocking
  again before Block 3, which needs ADR-004.
  
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

- [ ] **Block 3 · GIS Core** — Sprints 7–10. Sprint 7 (spatial database) is
  deferred by ADR-007; Sprints 8–10 (data download, GIS processing, tiling) all
  depend on ADR-004, so the block cannot be planned until the feasibility
  experiment above has run. Block 2 needs no further planning: DVC is deferred
  and Sprint 6 is absorbed into Sprint 2, so it closes with Sprint 4.

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
- [ ] **MLFLOW-STORE · The MLflow file store is in maintenance mode** — MLflow
  3.17.2 refuses to construct a `FileStore` without
  `MLFLOW_ALLOW_FILE_STORE=true` and names `sqlite:///mlflow.db` plus
  `mlflow migrate-filestore` as the supported destination. Sprint 4 opts in,
  inside the adapter, rather than carrying the database and dataframe stack
  eight sprints before its consumer
  ([ADR-008](architecture/adr/adr-008-experiment-tracking.md), amendment
  2026-10-27). `mlflow-skinny` cannot use a database backend at all — verified,
  not assumed — so the migration changes the distribution as well as the URI.
  Trigger: Sprint 12, the first real experiment, or any MLflow version bump,
  whichever comes first. Expect
  `test_a_non_file_uri_fails_with_the_vendor_error` to fail when the
  distribution is swapped: it asserts skinny's rejection of a `sqlite:` URI on
  purpose, as a tripwire, and is not a regression.
- [x] **CI-PIN · GitHub Actions pinned by tag, not by commit SHA** — resolved
  2026-10-25 in `d061937`: `actions/checkout` and `astral-sh/setup-uv` carry a
  commit digest with the version in a trailing comment, and both move together
  on a bump. Digest-pinning the container base image is a separate matter, under
  Known Issues in [current_state.md](current_state.md).
- [x] **TOOL-VERIF · `.agents/TOOLING.md` → Pending Verification was stale** —
  updated by the user on 2026-10-25: `dontAsk` (handoffs 007 and 008), the uv
  cache (`[tool.uv] cache-dir`, commit `dc769b9`) and the W2 and W3 results now
  sit in a new `## Verified` section. One honest unknown stays there, sandbox
  compatibility with Docker and package installation, to be confirmed from a
  container build or dropped.
- [x] **W2 · Secret pattern drift** — closed 2026-10-25 as resolved by design.
  The enumerated deny list exists to keep `.env.example` readable, since a deny
  rule cannot carve an exception, while the full `.env.*` glob is enforced by
  the working-tree guard from `secrets.include` (checked: `.env.staging` and
  `.env.whatever` classify as SECRET, `.env.example` does not). A missing deny
  entry costs a tool-level deny, never the guard's check. Stated in
  `.agents/TOOLING.md`.
- [x] **W3 · Permission coverage** — answered 2026-10-25: an `Edit(...)` deny
  does cover file writes. With `Edit(./.claude/**)` in the deny list and no
  `Write` rule, a `Write` to `.claude/skills/project-status/SKILL.md` was
  refused, and the shell route was refused by the sandbox as well. Recorded in
  `.agents/TOOLING.md` → `## Verified`.
- [x] **W12 · Redundant rule** — `Bash(git commit*--no-verify*)` was covered by
  the broader `Bash(git commit*)`; removed from `.claude/settings.json` by the
  user on 2026-10-25.

## Backlog

- [ ] Research state-of-the-art for abandoned infrastructure detection (Sprint 11;
  in MVP 1.0, to the depth the ADR-004 strategy decision needs).
- [ ] Evaluate PNOA/LiDAR data sources and download APIs (Sprint 8; first pass in
  the feasibility experiment above).
- [ ] Define abandonment indicators taxonomy (Sprint 14).

## Last Updated

2026-10-27
