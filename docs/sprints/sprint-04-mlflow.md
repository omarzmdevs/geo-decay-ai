# Sprint 04 · MLflow

## Block

Block 2 · MLOps and Data Infrastructure

## Goal

An experiment can be recorded before any experiment exists: the project holds a
tracking contract, one implementation against a local file store, and the wiring
that proves both work end to end — so that Sprint 12's first detector run logs
its parameters and metrics without any design decision left to make.

## Execution Mode

**Headless, three handoffs in order.** Nothing in this sprint touches a path
`.agents/policy.yaml` lists as protected: the work is confined to `src/`,
`tests/unit/`, `pyproject.toml`, `uv.lock` and `.env.example`, all inside the
developer scope. The user verifies a clean tree before each launch and reviews
the diff after.

## Requirements

* A tracking port in the domain, importing nothing but the standard library, so
  the domain-purity contract holds unchanged.
* One MLflow adapter and one null adapter in the data layer, selected by
  configuration; no layer below delivery reads configuration.
* `mlflow` importable from exactly one module, enforced by an import-linter
  contract rather than by convention.
* The store addressed by a configuration string, so moving to SQLite or to a
  server is not a code change.
* The minimum key set of [ADR-008](../architecture/adr/adr-008-experiment-tracking.md)
  — `bbox`, `bbox_crs`, `random_seed`, `git_commit`, `container_image_digest`,
  `config.json` — fixed before the first run, with capture only of what
  `Settings` already holds.
* A verified run: the sprint does not close on code that looks right, but on a
  run that exists in `mlruns/` with its parameters, metrics and tags readable
  back.

## Prerequisites

* [ADR-008](../architecture/adr/adr-008-experiment-tracking.md) — every decision
  the three handoffs apply; none of them re-decides anything.
* [ADR-007](../architecture/adr/adr-007-mvp-1-0-scope.md) — reduces this sprint
  to a local file store, defers DVC and absorbs Sprint 6.
* [ADR-006](../architecture/adr/adr-006-logging-strategy.md) — the
  composition-root pattern the tracker reuses.
* Sprint 2, handoff [007](../prompts/007-bounding-box-and-configuration.md) —
  the `Settings` object the new fields extend.
* Branch `block-2`, fast-forwarded to `main` at `3149453` (checked 2026-10-26).

## Tasks

- [x] [010](../prompts/010-experiment-tracking-port-and-config.md) — the port
      and the configuration. No tracking library enters the codebase.
- [x] [011](../prompts/011-mlflow-adapter-and-import-contract.md) — the MLflow
      and null adapters, the dependency and the import contract.
- [ ] [012](../prompts/012-tracking-composition-and-cli.md) — the composition
      root and the first CLI command, which records a real run.
- [ ] Orchestrator: verify each handoff against its criteria, re-run the gate,
      append the `## Verification` section; then run the documenter.
- [ ] User: review and commit each task's diff separately, in handoff order.
- [ ] Sprint close: fill the dates and the verdict here, update
      `current_state.md` and `next_tasks.md`, the `architecture.md` MLOps
      paragraph, and the directory index.

## Deliverable

`uv run geo-decay tracking-smoke` records a run in `mlruns/` under the
configured experiment, with the ADR-008 keys; the same command with
`GEO_DECAY_TRACKING_BACKEND=none` succeeds and records nothing; and
`lint-imports` fails if any module other than the adapter imports `mlflow`.

## Handoffs Executed

<!-- Completed as the sprint runs. -->

- [010 · Experiment-tracking port and configuration](../prompts/010-experiment-tracking-port-and-config.md) — ACCEPTED 2026-10-27 (orchestrator verification). Run by an in-process developer subagent (`sonnet`, planned tier `TIER_STANDARD`; the headless launch form was not used) from restore point `9a0390d`, outcome completed. Gate: `port and configuration ok` and all six pre-commit hooks passing on the tree as delivered (189 tests).
- [011 · MLflow adapter, null adapter and the import contract](../prompts/011-mlflow-adapter-and-import-contract.md) — ACCEPTED 2026-10-27 (orchestrator verification). Run by an in-process developer subagent (`sonnet`, planned tier `TIER_STANDARD`) in two runs: run 1 aborted on two defects of the handoff itself, and run 2 completed after the amendment of the same date. Run 1 from restore point `baef665`, outcome aborted; run 2 continued from run 1's working tree and has no restore point of its own, outcome completed. Gate: `adapters ok` and all six pre-commit hooks passing (200 tests, 5 import-linter contracts kept).

## Notes

* **The consumer is eight sprints away, and that is the central tension of this
  sprint.** ADR-007 forbids building before the consumer exists; comparability
  requires the key names to be fixed before the first run. The sprint resolves
  it by scope: the contract is complete, the implementation is the thinnest
  thing that can be verified, and automatic capture of the environment is left
  to the sprint that first needs it.
* **The base image is not digest-pinned** (user's decision, 2026-10-26, recorded
  as an ADR-005 amendment): the floating tag keeps security patches arriving
  automatically, and the digest is *recorded* per run instead, through
  `GEO_DECAY_CONTAINER_IMAGE_DIGEST`. This replaces the "digest-pin the base
  image" item under Known Issues in `current_state.md`, which the documenter
  rewrites at sprint close.
* **The MLflow UI is not a deliverable of this sprint.** It is a local developer
  tool, run from an isolated environment
  (`uvx --from mlflow mlflow ui --backend-store-uri ./mlruns`), outside the
  project's lockfile by design (ADR-008).
* **The bounding box stays reserved** (user, 2026-10-26). The smoke run needs
  *some* value for `GEO_DECAY_BBOX`, since Sprint 2 made it required; the
  verification commands supply a throwaway extent. Nothing in this sprint
  depends on its value, and the feasibility experiment remains out of the active
  slice.
* **Sprints 5 and 6 are not executed** and no handoff is written from them:
  deferred and absorbed respectively by ADR-007. Block 2 closes when Sprint 4
  does.
* **A deliberate tripwire (handoff 011).** `test_a_non_file_uri_fails_with_the_vendor_error`
  asserts that a `sqlite:` URI raises the vendor's `UnsupportedModelRegistryStoreURIException`,
  a property of `mlflow-skinny`, not of this code. It will fail when the MLFLOW-STORE
  migration swaps the distribution, so the test is revisited at that decision.
* **Run 2 of handoff 011 was launched from an uncommitted amendment.** The gate could not
  pass before the file-store opt-in existed, and `git commit --no-verify` is forbidden, so
  the amendment and the code land in one commit.

## Documents Updated

<!-- Completed as the sprint runs. -->

- [ADR-008](../architecture/adr/adr-008-experiment-tracking.md) — new, experiment tracking (2026-10-26)
- [ADR-005](../architecture/adr/adr-005-dependency-and-environment-manager.md) — amendment: base image recorded by digest, not pinned (2026-10-26)
- [docs/roadmap.md](../roadmap.md) — Sprint 4 scope note (2026-10-26)
- [docs/next_tasks.md](../next_tasks.md) — active sprint set to Sprint 4 (2026-10-26)
- [ADR-008](../architecture/adr/adr-008-experiment-tracking.md) amendment and [handoff 011](../prompts/011-mlflow-adapter-and-import-contract.md) amendment — `MLFLOW_ALLOW_FILE_STORE` opt-in and corrected criterion 2 (2026-10-27)

## Date Started

2026-10-26

## Date Completed

<!-- YYYY-MM-DD -->
