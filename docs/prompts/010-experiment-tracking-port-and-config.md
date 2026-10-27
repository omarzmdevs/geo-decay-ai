# Handoff 010 · Experiment-Tracking Port and Configuration

## Objective

The project declares how an experiment is recorded — as a domain port and as
validated configuration — without any tracking library entering the codebase.

## Role

developer

## Tier

`TIER_STANDARD` — small in volume, but the signatures are a contract that two
later handoffs implement and every later sprint calls, and the settings are
validated under strict typing.

## Context

Sprint 4, first of three handoffs: 011 implements the port, 012 wires it.
[ADR-008](../architecture/adr/adr-008-experiment-tracking.md) already decided
every question this task could raise — where the port lives, why it is a
`Protocol`, why the URI is a string, which keys a run records. Apply it; do not
re-decide it. If the ADR looks wrong, stop and report rather than improvising.

The one thing to notice while reading `config.py`: fields bind to their full
environment variable name through `validation_alias`, and the `before`
validators normalise case. Follow both conventions exactly.

## Files to Read

- `docs/architecture/adr/adr-008-experiment-tracking.md`
- `src/geo_decay_delivery/config.py`
- `tests/unit/delivery/test_config.py`
- `src/geo_decay_domain/bounding_box.py` — the domain's docstring and typing style

## Files to Create or Modify

- `src/geo_decay_domain/ports/__init__.py` *(new, empty docstring module)*
- `src/geo_decay_domain/ports/experiment_tracker.py` *(new)*
- `src/geo_decay_delivery/config.py` *(modify: four fields and their validators)*
- `.env.example` *(modify)*
- `tests/unit/domain/test_experiment_tracker_port.py` *(new)*
- `tests/unit/delivery/test_config.py` *(modify)*

## Out of Scope

- **MLflow in any form**: no dependency, no import, no mention in
  `pyproject.toml`. That is handoff 011, and `pyproject.toml` must not appear in
  this diff.
- Any implementation of the port beyond the throwaway stub a test needs.
- The composition root, the factory and the CLI (handoff 012).
- Capturing `git_commit` or `container_image_digest` automatically. ADR-008
  reserves the key names; this task only adds the field that carries the digest
  when the runner supplies it.
- The bounding box value, and anything to do with the feasibility experiment.
- `.gitignore`: `mlruns/` is already ignored, and no role owns that file.

## Execution Mode

Headless. No protected path is touched.

## Specification

### The port

`src/geo_decay_domain/ports/experiment_tracker.py`, standard library only:

```python
@runtime_checkable
class ExperimentTracker(Protocol):
    def start_run(
        self, name: str, *, tags: Mapping[str, str] | None = None
    ) -> AbstractContextManager[None]: ...
    def log_params(self, params: Mapping[str, object]) -> None: ...
    def log_metrics(
        self, metrics: Mapping[str, float], *, step: int | None = None
    ) -> None: ...
    def log_artifact(self, path: Path, *, subdir: str | None = None) -> None: ...
```

`Mapping` from `collections.abc`, `AbstractContextManager` from `contextlib`,
`Path` from `pathlib`, `Protocol` and `runtime_checkable` from `typing`.
`runtime_checkable` is required: it is how the verification checks the shape.
Document in the module docstring what each method is for, that a tracker is
obtained from the composition root and never constructed by the layer that uses
it, and that failures are not swallowed (ADR-008).

### The settings

Four fields in `Settings`, in the style the existing fields already use:

| Field | Type | Variable | Default |
|---|---|---|---|
| `tracking_backend` | `Literal["mlflow", "none"]` | `GEO_DECAY_TRACKING_BACKEND` | `"mlflow"` |
| `tracking_uri` | `str` | `GEO_DECAY_TRACKING_URI` | `"file:./mlruns"` |
| `tracking_experiment` | `str` | `GEO_DECAY_TRACKING_EXPERIMENT` | `"geo-decay"` |
| `container_image_digest` | `str \| None` | `GEO_DECAY_CONTAINER_IMAGE_DIGEST` | `None` |

Validators, each mirroring the shape of `_lower_log_format`:

- `tracking_backend`: strip and lowercase before validation.
- `tracking_uri` and `tracking_experiment`: strip; reject empty or
  whitespace-only with a message naming the variable, as the bbox validators do.
- `container_image_digest`: strip, and map empty string to `None` — the template
  ships the variable with no value, and `""` must not reach a run as a tag.

Add `TrackingBackend` as a module-level `Literal` alias beside `LogLevel` and
`LogFormat`, and `_TRACKING_*_VAR` constants only where a validator needs to
name a variable in its message.

### `.env.example`

Add the four variables to the `Geo-Decay Runtime Settings` block, each with a
one-line comment, in the style of the existing entries. Note on
`GEO_DECAY_TRACKING_URI` that an `http(s)` or `sqlite` URI switches the store
with no code change, and on `GEO_DECAY_CONTAINER_IMAGE_DIGEST` that whoever
starts the container supplies it (ADR-005 amendment 2026-10-26).

**Remove the stale `MLFLOW_TRACKING_URI` and `MLFLOW_EXPERIMENT_NAME` lines**
from the `MLOps & Tracking` block: they come from the original template, nothing
reads them, and two variable names for one setting is precisely the drift this
project avoids elsewhere. Leave a comment in that block pointing at the
`GEO_DECAY_TRACKING_*` variables.

### The tests

- `tests/unit/domain/test_experiment_tracker_port.py`: a minimal stub assigned
  to an `ExperimentTracker`-annotated name, so strict mypy checks the stub
  really satisfies the protocol, plus an `isinstance` assertion. The stub lives
  in the test file; no implementation is added to `src/`.
- `tests/unit/delivery/test_config.py`: defaults; each variable read from the
  environment; case and whitespace normalisation; an invalid backend raising
  `ValidationError`; empty digest becoming `None`. Follow the file's existing
  pattern for isolating the environment — and make sure no test can be
  influenced by a developer's real `.env`.

## Acceptance Tests

no — a declaration plus configuration validation. Unit tests cover the
behaviour and strict mypy checks the protocol's shape; ADR-008's criteria for
acceptance tests (abandonment index, georeferencing, detection, inter-stage data
contracts) do not apply.

## Acceptance Criteria

1. `geo_decay_domain.ports.experiment_tracker.ExperimentTracker` imports, is a
   runtime-checkable `Protocol` and exposes exactly `start_run`, `log_params`,
   `log_metrics` and `log_artifact`.
2. The port's source file contains no occurrence of `mlflow`, and imports only
   from `collections.abc`, `contextlib`, `pathlib` and `typing`.
3. `Settings()` with only the two required bbox variables set yields
   `tracking_backend == "mlflow"`, `tracking_uri == "file:./mlruns"`,
   `tracking_experiment == "geo-decay"` and `container_image_digest is None`.
4. Each of the four variables is read from the environment, and
   `GEO_DECAY_TRACKING_BACKEND=" MLflow "` yields `"mlflow"`.
5. `GEO_DECAY_TRACKING_BACKEND=sqlite`, `GEO_DECAY_TRACKING_URI=""` and
   `GEO_DECAY_TRACKING_EXPERIMENT="   "` each raise `ValidationError`.
6. `GEO_DECAY_CONTAINER_IMAGE_DIGEST=""` yields `None`.
7. `.env.example` contains the four `GEO_DECAY_TRACKING_*` /
   `GEO_DECAY_CONTAINER_IMAGE_DIGEST` names and no longer contains
   `MLFLOW_TRACKING_URI` or `MLFLOW_EXPERIMENT_NAME`.
8. `pyproject.toml`, `uv.lock` and every file under `src/geo_decay_data/`,
   `src/geo_decay_application/` and `tests/acceptance/` are unchanged.
9. `git status --short` lists only the six files above.
10. The full gate passes.

## Verification Command

```bash
uv run python - <<'PY'
import pathlib, typing
from pydantic import ValidationError
from geo_decay_domain.ports.experiment_tracker import ExperimentTracker
from geo_decay_delivery.config import Settings

src = pathlib.Path("src/geo_decay_domain/ports/experiment_tracker.py").read_text()
assert "mlflow" not in src.lower(), "the port must not mention mlflow"
for mod in ("osgeo", "rasterio", "pydantic", "geo_decay_delivery"):
    assert mod not in src, mod
assert typing.runtime_checkable(ExperimentTracker) is ExperimentTracker
methods = {n for n in vars(ExperimentTracker) if not n.startswith("_")}
assert methods == {"start_run", "log_params", "log_metrics", "log_artifact"}, methods

base = {"GEO_DECAY_BBOX": "0,0,1,1", "GEO_DECAY_BBOX_CRS": "EPSG:4326"}
def settings(**over: str) -> Settings:
    return Settings(_env_file=None, **{**base, **over})  # type: ignore[call-arg]

s = settings()
assert (s.tracking_backend, s.tracking_uri, s.tracking_experiment) == (
    "mlflow", "file:./mlruns", "geo-decay"), s
assert s.container_image_digest is None

assert settings(GEO_DECAY_TRACKING_BACKEND=" MLflow ").tracking_backend == "mlflow"
assert settings(GEO_DECAY_TRACKING_BACKEND="none").tracking_backend == "none"
assert settings(GEO_DECAY_TRACKING_URI="sqlite:///m.db").tracking_uri == "sqlite:///m.db"
assert settings(GEO_DECAY_TRACKING_EXPERIMENT=" run-a ").tracking_experiment == "run-a"
assert settings(GEO_DECAY_CONTAINER_IMAGE_DIGEST="").container_image_digest is None
assert settings(GEO_DECAY_CONTAINER_IMAGE_DIGEST="sha256:ab").container_image_digest == "sha256:ab"

for bad in (
    {"GEO_DECAY_TRACKING_BACKEND": "sqlite"},
    {"GEO_DECAY_TRACKING_URI": ""},
    {"GEO_DECAY_TRACKING_EXPERIMENT": "   "},
):
    try:
        settings(**bad)
    except ValidationError:
        continue
    raise AssertionError(f"accepted invalid value: {bad}")

env = pathlib.Path(".env.example").read_text()
for name in (
    "GEO_DECAY_TRACKING_BACKEND", "GEO_DECAY_TRACKING_URI",
    "GEO_DECAY_TRACKING_EXPERIMENT", "GEO_DECAY_CONTAINER_IMAGE_DIGEST",
):
    assert name in env, name
for stale in ("MLFLOW_TRACKING_URI", "MLFLOW_EXPERIMENT_NAME"):
    assert stale not in env, stale
print("port and configuration ok")
PY
uv run pre-commit run --all-files && git status --short && git diff --stat
```

The last two commands prove criteria 8–10: the gate includes import-linter, so a
domain-purity violation fails here rather than in review.

## Launch Command

```bash
claude -p "ROLE: developer. Execute docs/prompts/010-experiment-tracking-port-and-config.md" \
  --model sonnet --permission-mode dontAsk \
  --allowedTools "Read" "Edit" "Write" "Glob" "Grep" \
    "Bash(uv run *)" \
    "Bash(git status*)" "Bash(git diff*)" < /dev/null
```

No `uv sync` or `uv lock`: this task adds no dependency.

## Restore Point

`3149453` — `Merge pull request #1 from omarzmdevs/bloque-1`, the state of
`block-2` when the sprint was planned. The launch point is the commit in which
the user freezes this sprint's plan (this handoff, 011, 012, ADR-008, the
ADR-005 amendment and the sprint log); whoever launches records that SHA in the
run record and confirms a clean tree first.

---

## Run Record

Date:
Tool and model:
Restore point:
Outcome: <!-- completed | failed | aborted -->

## Verification

Verdict: <!-- ACCEPTED | REJECTED -->
Files changed:
Gate:
Notes:
