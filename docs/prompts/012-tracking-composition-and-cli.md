# Handoff 012 · Tracking Composition Root and the First CLI Command

## Objective

Delivery builds the tracker from configuration and injects it, and a CLI command
records a real run with the ADR-008 keys, which is what proves the sprint.

## Role

developer

## Tier

`TIER_STANDARD` — the composition root, the project's first executable entry
point and an end-to-end test. Each piece is small; together they are what makes
Sprint 4 true rather than plausible.

## Context

Sprint 4, last of three handoffs. Handoff 010 delivered the port and the
settings, 011 the two adapters and the import contract; nothing yet connects
them, and no run has ever been recorded.

This handoff follows the pattern ADR-006 already established for logging: the
entry point builds `Settings`, configures logging once, and passes what it built
downwards. `configure_logging` is the precedent to imitate, down to the shape of
its docstring.

**On the bounding box.** `Settings` requires `GEO_DECAY_BBOX` and
`GEO_DECAY_BBOX_CRS` and has no defaults for them (Sprint 2), so the smoke
command needs *some* extent. The verification supplies a throwaway one. The real
extent is reserved by the user and nothing here depends on its value — do not
add a default, and do not touch the bbox fields.

## Files to Read

- `docs/architecture/adr/adr-008-experiment-tracking.md`
- `src/geo_decay_delivery/config.py`
- `src/geo_decay_delivery/logging_config.py`
- `src/geo_decay_domain/ports/experiment_tracker.py`
- `src/geo_decay_data/tracking/mlflow_tracker.py`
- `pyproject.toml`

## Files to Create or Modify

- `src/geo_decay_delivery/tracking.py` *(new: the factory)*
- `src/geo_decay_delivery/cli/main.py` *(new: the entry point)*
- `pyproject.toml` *(modify: `[project.scripts]` only)*
- `tests/unit/delivery/test_tracking.py` *(new)*
- `tests/unit/delivery/test_cli.py` *(new)*

## Out of Scope

- Any CLI framework. `argparse` from the standard library, for the same reason
  ADR-006 chose the standard library for logging: nothing in this sprint needs
  more, and a framework adopted without a consumer is a dependency to justify
  later.
- Any second command, and any pipeline step. One command, whose only job is to
  prove the wiring.
- Changing the port, the adapters, `Settings`, `.env.example` or any
  import-linter contract. The contract from 011 must still pass unchanged:
  delivery imports the *adapters*, never `mlflow`.
- Adding a dependency. `pyproject.toml` changes by exactly one table entry.
- Capturing `git_commit` automatically; it stays reserved (ADR-008).
- Reading or printing a secret. The `config.json` artifact carries the resolved
  tracking and runtime settings — never an API key, a password or a connection
  string.

## Execution Mode

Headless. No protected path is touched.

## Specification

### The factory

`src/geo_decay_delivery/tracking.py`:

```python
def build_tracker(settings: Settings) -> ExperimentTracker: ...
```

Returns `MlflowTracker(settings.tracking_uri, settings.tracking_experiment)` for
backend `mlflow` and `NullTracker()` for `none`. The return type is the port, so
no caller can depend on which implementation it got. Because
`tracking_backend` is a `Literal` of two values, the branch is exhaustive —
write it so mypy can see that, with no `else: raise` that strict mypy would
report as unreachable. Log at INFO which backend was selected: an operator who
believes a run is being recorded when the backend is `none` is the one failure
mode this sprint can introduce.

### The entry point

`src/geo_decay_delivery/cli/main.py`, with `main(argv: Sequence[str] | None = None) -> int`:

1. Parse arguments with `argparse`: the program is `geo-decay`, with one
   subcommand, `tracking-smoke`.
2. Build `Settings()`, then `configure_logging(settings)` — once, here.
3. `build_tracker(settings)`.
4. Open a run named `tracking-smoke` and record exactly the ADR-008 minimum that
   `Settings` can supply today:
   - params `bbox` (the four coordinates as the configured string form),
     `bbox_crs`, `random_seed`;
   - tag `container_image_digest`, **only when it is not `None`**;
   - metric `smoke` with value `1.0`, so the run carries at least one metric;
   - artifact `config.json`: the resolved settings serialised, written to a
     temporary directory and logged from there.
5. Log the run's identifier at INFO, or state that the backend recorded nothing.
6. Return `0` on success. A `ValidationError` from `Settings` returns `2` with a
   message naming the variable — the caller has forgotten configuration, which
   is not a crash to a traceback.

Add to `pyproject.toml`:

```toml
[project.scripts]
geo-decay = "geo_decay_delivery.cli.main:main"
```

`uv sync` after adding it, or the console script will not exist.

### The tests

- `test_tracking.py`: each backend returns the expected type, typed as the port.
- `test_cli.py`: `main(["tracking-smoke"])` with a monkeypatched environment
  pointing at `tmp_path` returns `0` and the run is readable back through
  `MlflowClient` with the three params and the metric; with
  `GEO_DECAY_TRACKING_BACKEND=none` it returns `0` and writes nothing; with the
  digest set, the tag is present; without it, the tag is absent; missing bbox
  configuration returns `2`; `--help` exits `0`. Note that `test_cli.py` imports
  `MlflowClient` — a test file, outside the four packages, so the import
  contract does not apply.

## Acceptance Tests

no — wiring and one executable command, covered end to end by unit tests and by
the verification below.

## Acceptance Criteria

1. `uv run geo-decay --help` exits `0` and names `tracking-smoke`.
2. With a `file:` store in a temporary directory,
   `uv run geo-decay tracking-smoke` exits `0` and creates exactly one run under
   the configured experiment.
3. That run carries params `bbox`, `bbox_crs` and `random_seed`, the metric
   `smoke`, and `config.json` among its artifacts.
4. With `GEO_DECAY_CONTAINER_IMAGE_DIGEST` set, the run carries it as a tag;
   with the variable absent, no such tag exists.
5. With `GEO_DECAY_TRACKING_BACKEND=none`, the command exits `0` and creates no
   file in the tracking directory.
6. With `GEO_DECAY_BBOX` unset, the command exits `2` and its output names the
   variable.
7. `config.json` contains no value of any variable whose name contains `KEY`,
   `TOKEN`, `SECRET` or `PASSWORD`.
8. `pyproject.toml`'s only change is the `[project.scripts]` table; no
   dependency and no contract changed.
9. `git status --short` lists only the five files above, plus `uv.lock` if
   `uv sync` touched it.
10. The full gate passes, with the `MLflow is confined to its adapter` contract
    still green.

## Verification Command

```bash
uv sync
set -e
RUNS="$(mktemp -d)/runs"
export GEO_DECAY_BBOX="0,0,1,1" GEO_DECAY_BBOX_CRS="EPSG:4326"
export GEO_DECAY_TRACKING_URI="file:$RUNS" GEO_DECAY_TRACKING_EXPERIMENT="verify-012"
uv run geo-decay --help | grep -q "tracking-smoke"
GEO_DECAY_CONTAINER_IMAGE_DIGEST="sha256:feedface" uv run geo-decay tracking-smoke
uv run python - <<'PY'
import os, pathlib
from mlflow.tracking import MlflowClient

store = f"file:{os.environ['GEO_DECAY_TRACKING_URI'].removeprefix('file:')}"
client = MlflowClient(tracking_uri=store)
experiment = client.get_experiment_by_name("verify-012")
assert experiment is not None, "no experiment was created"
runs = client.search_runs([experiment.experiment_id])
assert len(runs) == 1, runs
run = runs[0]
for key in ("bbox", "bbox_crs", "random_seed"):
    assert key in run.data.params, (key, run.data.params)
assert run.data.metrics["smoke"] == 1.0, run.data.metrics
assert run.data.tags.get("container_image_digest") == "sha256:feedface", run.data.tags
artifacts = [f.path for f in client.list_artifacts(run.info.run_id)]
assert "config.json" in artifacts, artifacts
local = pathlib.Path(client.download_artifacts(run.info.run_id, "config.json"))
body = local.read_text().upper()
for forbidden in ("KEY", "TOKEN", "SECRET", "PASSWORD"):
    assert forbidden not in body, forbidden
print("smoke run ok")
PY
NONE_RUNS="$(mktemp -d)/none"
GEO_DECAY_TRACKING_BACKEND=none GEO_DECAY_TRACKING_URI="file:$NONE_RUNS" \
  uv run geo-decay tracking-smoke
test ! -d "$NONE_RUNS" && echo "none backend wrote nothing"
env -u GEO_DECAY_BBOX uv run geo-decay tracking-smoke 2>&1 | grep -q "GEO_DECAY_BBOX" \
  && echo "missing configuration names the variable"
env -u GEO_DECAY_BBOX uv run geo-decay tracking-smoke; test $? -eq 2 && echo "exit code 2 ok"
uv run pre-commit run --all-files && git status --short && git diff --stat
```

Run it from a clean tree: it writes only into temporary directories, but it does
create `mlruns/` if a step is misconfigured, and that must not reach a commit.

## Launch Command

```bash
claude -p "ROLE: developer. Execute docs/prompts/012-tracking-composition-and-cli.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" "Bash(uv sync*)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

`uv sync` is allowed — adding `[project.scripts]` requires reinstalling the
package for the console script to appear — but `uv lock` is not: no dependency
changes here.

## Restore Point

The commit in which handoff 011 was accepted and committed. Whoever launches
confirms a clean tree and records the SHA here.

## Follow-up for the User

1. Review the diff and commit it.
2. Inspect the runs in the UI if you want to see them:
   `MLFLOW_ALLOW_FILE_STORE=true uvx --from mlflow mlflow ui --backend-store-uri ./mlruns`. It needs network
   access the first time and is deliberately outside the project environment
   (ADR-008).
3. Confirm `mlruns/` is absent from the commit — it is gitignored, and that is
   worth checking once, here.

---

## Amendment 2026-10-27 · Three Defects in the Verification Command

The delivery was correct; the verification command was not. All three defects
are the orchestrator's, found by the developer and confirmed independently.

1. **The reader process needs the opt-in.** The script opens the store with a
   plain `MlflowClient` in a separate process, and only the adapter sets
   `MLFLOW_ALLOW_FILE_STORE`, so MLflow refuses to open it. The guard is in
   `FileStore.__init__`, which every reader goes through — verified by
   constructing `FileStore` without the variable, which raises. The preamble
   therefore exports `MLFLOW_ALLOW_FILE_STORE=true`. A verification command is
   not repository code, so the containment rule, which covers `src/**`, is
   untouched. The same correction applies to the UI command in the follow-up
   below and in ADR-008.
2. **`set -e` aborts the script at the exit-code check.**
   `env -u GEO_DECAY_BBOX uv run geo-decay tracking-smoke; test $? -eq 2` runs a
   command that is *meant* to fail, so `set -e` ends the script before the test.
   The check must be wrapped in `set +e` (or written as
   `if ! …; then`), and the steps after it were never reached.
3. **`mktemp -d` is unavailable in the agent sandbox**, which ignores `TMPDIR`
   on macOS. Use `mkdir -p "$TMPDIR/<name>"`.

Criterion 7 was also strengthened when re-run: rather than trusting that no
secret *can* reach `config.json`, the orchestrator exported four real-looking
secrets — an API key, a session secret, a database password and a token — and
asserted that neither their names nor their values appear in the artifact.

---

## Run Record

Date: 2026-10-27
Tool and model: in-process developer subagent (`sonnet`, planned
`TIER_STANDARD`), launched from the orchestrator's interactive session.
Restore point: `20f9db1` — `feat(tracking): add MLflow and null adapters with an
import confinement contract (handoff 011)`. Working tree clean at launch.
Outcome: completed, with the verification command's three defects worked around
and reported rather than silently patched.

## Verification

Verdict: **ACCEPTED**

Files changed — five, as the handoff lists:

| File | |
|---|---|
| `src/geo_decay_delivery/tracking.py` | new, `build_tracker` on an exhaustive `match` |
| `src/geo_decay_delivery/cli/main.py` | new, `argparse`, one subcommand |
| `pyproject.toml` | `[project.scripts]` only, three lines |
| `tests/unit/delivery/test_tracking.py` | new |
| `tests/unit/delivery/test_cli.py` | new |

`uv.lock` is unchanged, no dependency was added, and no import-linter contract
was touched.

Gate, re-run by the orchestrator: all six hooks pass, 213 tests. `grep` over
`src/` finds `import mlflow` and `MLFLOW_ALLOW_FILE_STORE` in the adapter and
nowhere else, so delivery composes the adapters without knowing the vendor.
`mlruns/` does not exist in the repository root.

Criteria, checked one by one with the corrected command:

1. `geo-decay --help` exits 0 and names `tracking-smoke`. ✔
2. The smoke run exits 0 and creates exactly one run in the configured
   experiment. ✔
3. The run carries `bbox`, `bbox_crs`, `random_seed`, the metric `smoke` and
   `config.json`. ✔
4. The digest is a tag when the variable is set, and absent when it is not —
   both directions checked, on two separate runs. ✔
5. `GEO_DECAY_TRACKING_BACKEND=none` exits 0 and the tracking path is never
   created. ✔
6. With `GEO_DECAY_BBOX` unset the command exits 2 and names the variable. ✔
7. No secret reaches `config.json`: with `ANTHROPIC_API_KEY`, `SECRET_KEY`,
   `POSTGRES_PASSWORD` and `GITHUB_TOKEN` set in the environment, neither the
   words `KEY`, `TOKEN`, `SECRET`, `PASSWORD` nor any of their values appear in
   the artifact. Its keys are exactly the ten-field allowlist. ✔
8. `pyproject.toml` changed only in `[project.scripts]`. ✔
9. `git status --short` lists only the five files. ✔
10. The full gate passes. ✔

Notes:

- **Four deviations, all accepted, two of them improvements on the
  specification.**
  - `config.json` is built from an **explicit allowlist** rather than
    `model_dump()`. The handoff did not say which; the allowlist is the better
    choice, because a secret added to `Settings` later cannot reach a run by
    default. The cost — a new field is not recorded until someone lists it — is
    stated in the function's docstring, which is where a future reader will
    look.
  - The recorded `tracking_uri` has any `user:pass@` part **stripped**. Beyond
    the specification, and right: the day the URI points at a server, the
    artifact would otherwise carry a credential into every run.
  - **No run identifier is logged.** The handoff asked for it; the port exposes
    none, and changing the port was out of scope, so the CLI logs the experiment
    name instead. The developer reported this rather than importing `mlflow`
    into delivery to get the id, which would have broken the contract to satisfy
    a log line. Recorded as **PORT-RUNID** in `next_tasks.md`.
  - A `mktemp` shim on `PATH` during the run, environmental only, caused by
    defect 3 above.
- **The `none` branch was checked for silence, not just for exit 0:** the
  tracking path is not created at all, and the CLI says in its log that nothing
  was recorded. That line is the difference between a deliberate unrecorded run
  and an operator who thinks an experiment exists.
- `build_tracker` returns the port type and matches exhaustively on a
  two-value `Literal`, so adding a third backend is a type error at the match
  rather than a silent `None` at runtime.
