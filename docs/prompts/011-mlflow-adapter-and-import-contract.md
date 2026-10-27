# Handoff 011 · MLflow Adapter, Null Adapter and the Import Contract

## Objective

The tracking port has two implementations — MLflow against a local file store
and a null tracker — and `mlflow` is importable from exactly one module,
enforced by the quality gate.

## Role

developer

## Tier

`TIER_STANDARD` — an adapter over a third-party API, a dependency change, an
import-linter contract and tests that read a run back from a file store. Routine
work, but a mistake in the contract is invisible without running the gate.

## Context

Sprint 4, second of three handoffs. Handoff 010 added the port; nothing calls it
yet, which is handoff 012. Apply
[ADR-008](../architecture/adr/adr-008-experiment-tracking.md) and do not
re-decide it: the adapter belongs to the data layer, takes plain values rather
than `Settings`, swallows no exception, and `mlflow` stays confined to one
module.

**One empirical question this task settles.** ADR-008 chooses `mlflow-skinny`,
the client-only distribution, so the project's lockfile does not carry a web
framework. Whether that distribution can write and read a `file:` store is
exactly what criterion 4 checks. **If it cannot, replace it with the full
`mlflow` package, say so in the run record, and continue** — that is a recorded
deviation, not a failure. Do not install both: they provide the same import name
and would collide.

## Files to Read

- `docs/architecture/adr/adr-008-experiment-tracking.md`
- `src/geo_decay_domain/ports/experiment_tracker.py`
- `pyproject.toml`
- `src/geo_decay_delivery/logging_config.py` — the module docstring and
  error-handling style to match

## Files to Create or Modify

- `src/geo_decay_data/tracking/__init__.py` *(new)*
- `src/geo_decay_data/tracking/mlflow_tracker.py` *(new)*
- `src/geo_decay_data/tracking/null_tracker.py` *(new)*
- `tests/unit/data/tracking/test_mlflow_tracker.py` *(new)*
- `tests/unit/data/tracking/test_null_tracker.py` *(new)*
- `pyproject.toml` *(modify: dependency, import-linter contract, mypy override only if needed)*
- `uv.lock` *(regenerated)*

## Out of Scope

- The composition root, the factory, the CLI and `[project.scripts]` — handoff
  012. No file under `src/geo_decay_delivery/` appears in this diff.
- `Settings`, `.env.example` and the port: handoff 010 delivered them and they
  are not revisited. If the port is wrong, stop and report.
- The full `mlflow` package as a *project* dependency, unless criterion 4 forces
  it; the UI is never a project dependency.
- Any dependency beyond the tracking client. No pandas, no numpy, no
  `mlflow[extras]`.
- Capturing git SHA or image digest, retry logic, batching, autologging, and the
  Model Registry.
- Changing the existing `Domain purity` contract or any other contract already
  in `pyproject.toml`.

## Execution Mode

Headless. No protected path is touched.

## Specification

### `MlflowTracker`

Constructor `MlflowTracker(tracking_uri: str, experiment: str)`, which sets the
tracking URI and selects (creating if absent) the experiment. It must not import
`geo_decay_delivery`, read the environment or touch `Settings`: ADR-006's rule
that no layer below delivery reads configuration applies here too.

- `start_run` is a `@contextmanager` wrapping `mlflow.start_run(run_name=name)`,
  applying `tags` when given, and yielding `None`.
- `log_params`, `log_metrics` and `log_artifact` delegate to the fluent API.
  `log_metrics` forwards `step` only when it is not `None`.
- No `try/except` around any MLflow call. A tracking failure is loud (ADR-008).
- Keep to `import mlflow` and the fluent API where possible. If a submodule
  import is unavoidable, add the matching `ignore_imports` line.

### `NullTracker`

The same port, doing nothing: `start_run` is a context manager that yields, the
log methods return immediately. No filesystem access, no logging side effect, no
`mlflow` import. Its docstring states its two uses — tests, and
`GEO_DECAY_TRACKING_BACKEND=none` for a deliberate run without a record.

### `pyproject.toml`

1. `dependencies = ["pydantic-settings", "mlflow-skinny"]` — a bare name, no
   version ceiling, pinned by `uv.lock` as every other dependency is.
   Regenerate with `uv lock` and install with `uv sync`.
2. A new import-linter contract, left exactly as named here so the verification
   can find it:

```toml
[[tool.importlinter.contracts]]
name = "MLflow is confined to its adapter"
type = "forbidden"
source_modules = [
    "geo_decay_domain",
    "geo_decay_data",
    "geo_decay_application",
    "geo_decay_delivery",
]
forbidden_modules = ["mlflow"]
ignore_imports = ["geo_decay_data.tracking.mlflow_tracker -> mlflow"]
```

   It overlaps the existing `Domain purity` contract, which also names `mlflow`.
   That is deliberate: domain purity is the broader statement and stays as it is.
3. A mypy override for `mlflow.*` **only if strict mypy fails without one**. If
   you add it, keep it to `ignore_missing_imports` and record in the run record
   which error forced it — ADR-008's reason for confining the vendor to one
   module is that this `Any` stays contained.

### The tests

Against a `file:` store under pytest's `tmp_path`; nothing may be written inside
the repository. Read the run back through `mlflow.tracking.MlflowClient` rather
than `search_runs`, which returns a pandas frame the skinny distribution may not
have. Cover: a run appears under the configured experiment; params, metrics and
tags round-trip; `log_artifact` stores a file written into `tmp_path`;
`step` reaches a metric's history; the null tracker accepts the same calls, is
accepted as an `ExperimentTracker` and creates no directory.

## Acceptance Tests

no — adapter code over a third-party API, covered by unit tests against a real
file store.

## Acceptance Criteria

1. `MlflowTracker` and `NullTracker` both satisfy `ExperimentTracker` (strict
   mypy, plus an `isinstance` check).
2. No module under `src/` other than
   `src/geo_decay_data/tracking/mlflow_tracker.py` contains the string `mlflow`.
3. `pyproject.toml` contains a contract named `MLflow is confined to its
   adapter`, and `lint-imports` passes.
4. A run logged through `MlflowTracker` into a temporary `file:` store is
   readable back with its params, metrics and tags.
5. `NullTracker` performs the same calls without creating any path.
6. `mlflow-skinny` (or `mlflow`, if criterion 4 forced it) is in
   `[project.dependencies]` and in `uv.lock`; `uv sync --frozen` succeeds, so
   the manifest and the lockfile agree.
7. No file under `src/geo_decay_delivery/`, `src/geo_decay_application/`,
   `src/geo_decay_domain/`, `.env.example` or `tests/acceptance/` is changed.
8. `git status --short` lists only the seven files above.
9. The full gate passes.

## Verification Command

```bash
uv sync --frozen
uv run python - <<'PY'
import pathlib, tempfile
from mlflow.tracking import MlflowClient
from geo_decay_domain.ports.experiment_tracker import ExperimentTracker
from geo_decay_data.tracking.mlflow_tracker import MlflowTracker
from geo_decay_data.tracking.null_tracker import NullTracker

adapter = pathlib.Path("src/geo_decay_data/tracking/mlflow_tracker.py")
offenders = [
    str(p) for p in pathlib.Path("src").rglob("*.py")
    if "mlflow" in p.read_text().lower() and p != adapter
]
assert not offenders, offenders
assert "MLflow is confined to its adapter" in pathlib.Path("pyproject.toml").read_text()

tmp = pathlib.Path(tempfile.mkdtemp())
store = f"file:{tmp / 'runs'}"
tracker: ExperimentTracker = MlflowTracker(store, "verify-011")
artifact = tmp / "note.txt"
artifact.write_text("hello")
with tracker.start_run("smoke", tags={"stage": "verify"}):
    tracker.log_params({"a": 1, "b": "two"})
    tracker.log_metrics({"m": 0.5})
    tracker.log_metrics({"m": 0.25}, step=1)
    tracker.log_artifact(artifact)

client = MlflowClient(tracking_uri=store)
experiment = client.get_experiment_by_name("verify-011")
assert experiment is not None, "experiment was not created"
runs = client.search_runs([experiment.experiment_id])
assert len(runs) == 1, runs
run = runs[0]
assert run.data.params == {"a": "1", "b": "two"}, run.data.params
assert run.data.tags["stage"] == "verify"
assert run.info.run_name == "smoke", run.info.run_name
history = client.get_metric_history(run.info.run_id, "m")
assert {(m.step, m.value) for m in history} == {(0, 0.5), (1, 0.25)}, history
assert "note.txt" in [f.path for f in client.list_artifacts(run.info.run_id)]

null: ExperimentTracker = NullTracker()
before = sorted(p.name for p in tmp.iterdir())
with null.start_run("nothing", tags={"stage": "verify"}):
    null.log_params({"a": 1})
    null.log_metrics({"m": 1.0}, step=3)
    null.log_artifact(artifact)
assert sorted(p.name for p in tmp.iterdir()) == before, "NullTracker wrote something"
assert isinstance(null, ExperimentTracker) and isinstance(tracker, ExperimentTracker)
print("adapters ok")
PY
uv run pre-commit run --all-files && git status --short && git diff --stat
```

`uv sync --frozen` first: it fails if `uv.lock` no longer matches
`pyproject.toml`, which is criterion 6. The gate then runs `lint-imports`,
which is criterion 3.

## Launch Command

```bash
claude -p "ROLE: developer. Execute docs/prompts/011-mlflow-adapter-and-import-contract.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" "Bash(uv sync*)" "Bash(uv lock*)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

`uv sync` and `uv lock` are allowed because this task changes dependencies
(`.agents/TOOLING.md`). The sandbox already allows `pypi.org` and
`files.pythonhosted.org`.

## Restore Point

The commit in which handoff 010 was accepted and committed. Whoever launches
confirms a clean tree and records the SHA here: 011 depends on 010's port, so
the two tasks are never in the same diff.

---

## Run Record

Date:
Tool and model:
Restore point:
Distribution installed and resolved version: <!-- mlflow-skinny or mlflow, and why -->
Outcome: <!-- completed | failed | aborted -->

## Verification

Verdict: <!-- ACCEPTED | REJECTED -->
Files changed:
Gate:
Notes:
