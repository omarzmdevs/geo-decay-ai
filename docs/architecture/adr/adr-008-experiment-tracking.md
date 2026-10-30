# ADR-008: Experiment Tracking

## Status

Accepted

## Date

2026-10-26

## Context

Sprint 4 is the only sprint of Block 2 that MVP 1.0 executes: ADR-007 reduces
MLflow to a local file store, defers DVC in favour of an acquisition manifest
(Sprint 8) and absorbs Sprint 6 into Sprint 2. Four constraints shape what is
left.

**The consumer does not exist yet.** The first real experiment is Sprint 12
(detector) and the first comparison is Sprint 19. ADR-007's rule — nothing is
built before the sprint that first needs it — argues for building almost
nothing. But the *contract* must exist before the first run, because runs
recorded under different key names are not comparable, and a thesis that cannot
compare its own runs has no results section. The resolution is to fix the
contract now and keep the implementation to the thinnest thing that can be
verified end to end.

**Layer boundaries are enforced, not advisory.** ADR-003 keeps the four layers
independent and import-linter checks it in the gate; the domain-purity contract
already names `mlflow` among the libraries the domain may not import. Any
tracking solution either respects that or changes the contracts.

**Tracking is not logging.** ADR-006 already drew this line: logging answers
*what the process did and where it failed*, tracking answers *what was measured
under which inputs*. The two are configured in the same place — the composition
root — and share nothing else.

**Reproducibility has to survive the thesis defence.** A result must be
traceable, from the repository alone, to the inputs and the environment that
produced it, a year after the run. That requirement falls on this ADR because
the run record is where that evidence lands.

## Decision

**MLflow, local file store, with the store as configuration.** The tracking URI
is a `str` setting defaulting to `file:./mlruns` (already gitignored). It is a
string rather than a `Path` so that `sqlite:///mlflow.db` or
`https://tracking.example` is a change of configuration and not of code. This
single choice is what makes every alternative in the next section reversible,
and it is why none of them has to be decided now.

**The port is a domain `Protocol`.** `geo_decay_domain.ports.experiment_tracker`
declares `start_run`, `log_params`, `log_metrics` and `log_artifact` and imports
nothing but the standard library, so the domain-purity contract holds unchanged.
This follows the convention already stated in `architecture.md`: ports are
defined in the domain, the data layer implements them, and application and data
never import each other.

**The adapter lives in the data layer.** `geo_decay_data.tracking` holds
`MlflowTracker` and, beside it, `NullTracker`. The data layer is the project's
I/O and persistence layer; delivery is "FastAPI, the map and the CLI,
interchangeable", and a tracking adapter is not an interchangeable delivery
mechanism. The adapter takes plain values (`tracking_uri`, `experiment`) and
never imports `Settings`: no layer below delivery reads configuration (ADR-006).

**`mlflow` is confined by contract.** An import-linter `forbidden` contract
names `mlflow` for all four root packages with a single `ignore_imports`
exception for the adapter module. The boundary is then checked on every commit
instead of resting on discipline, and MLflow's incomplete type coverage — if it
needs a mypy override — stays contained in one file instead of leaking `Any`
across the codebase.

**Delivery composes, exactly as it does for logging.** The entry point builds
`Settings`, calls `configure_logging`, builds the tracker from
`tracking_backend` and injects it. `none` selects `NullTracker`, which is what
makes tests, offline work and "run the pipeline without recording" possible
without a single conditional at the call sites.

**Tracking failures are loud.** The adapter catches nothing. A silent failure
would leave the operator believing an experiment was recorded when it was not,
which is worse than a crash; ADR-007's "degrade instead of block" is about
unavailable *data* routes, not about losing the record of a run. Running without
tracking is expressed by choosing the `none` backend, deliberately.

**Every run records a minimum set of keys**, reserved here so that Sprints 12
and 19 do not invent their own:

| Kind | Keys |
|---|---|
| Params | `bbox`, `bbox_crs`, `random_seed` |
| Tags | `git_commit`, `container_image_digest` |
| Artifact | `config.json` — the resolved settings, secrets excluded |

The key names are fixed now; **automatic capture arrives with the sprint that
needs it.** Sprint 4 logs what `Settings` already holds and leaves the rest
optional, because a git-SHA helper with no experiment to attach it to is exactly
the speculative work ADR-007 forbids.

**`container_image_digest` is supplied, not discovered.** A process cannot
reliably learn the digest of the image it is running in, so it arrives as
`GEO_DECAY_CONTAINER_IMAGE_DIGEST`, set by whoever starts the container. See the
ADR-005 amendment of the same date: the base image stays on its floating tag so
security patches keep arriving automatically, and reproducibility is served by
*recording* the digest that produced a result rather than by freezing it.

**The client is installed, not the server.** `mlflow-skinny` is the project
dependency: it is the tracking client, without Flask, the web server and the
model flavours. The UI is a local developer tool, run from an isolated
environment (`MLFLOW_ALLOW_FILE_STORE=true uvx --from mlflow mlflow ui --backend-store-uri ./mlruns`), so a
visualisation concern does not add dozens of transitive packages to the lockfile
that the container and CI install. If the skinny distribution cannot write a
file store, the full `mlflow` package replaces it and the deviation is recorded
in the run record.

**The Model Registry is out of scope.** It requires a SQL backend; the file
store cannot serve it. Model versioning in MVP 1.0 is a logged artifact plus the
run that produced it.

## Alternatives Considered

**A managed platform — Weights & Biases, Neptune, Comet, DagsHub.** Better
dashboards, zero operation, and genuinely better collaboration. Rejected on two
grounds that matter more here: an API key in the environment, which the agent
sandbox is configured never to read, and the evidence of the thesis moving to a
third party whose retention and pricing are outside the project. The repository
has to remain self-sufficient evidence.

**A self-hosted MLflow server (Docker Compose) from the start.** Needed for
concurrent clients or a shared registry. Rejected: one developer, one process.
It is a service to operate in exchange for a feature set nothing uses — and the
tracking URI makes it a later configuration change.

**DVC now, as the roadmap originally scheduled.** Rejected by ADR-007 and not
reopened: DVC answers "fetch exactly this dataset", while the open question here
is "where did this file come from and what does it contain", which a manifest
with source URL, date, extent and checksum answers without a remote to
configure, a second dependency graph to maintain or a `dvc pull` in every
environment.

**No port: call `mlflow` directly from wherever a metric appears.** The smallest
diff today. Rejected: it spreads a vendor API across layers whose independence
is enforced in the gate, makes the `none` backend impossible without
conditionals everywhere, and turns any later change of tool into a sweep through
the codebase.

**The adapter in delivery instead of the data layer.** Tempting, since delivery
already holds configuration and logging. Rejected: the application layer could
then never record a metric without inverting the dependency a second time, and
it misreads delivery's role, which is interchangeable presentation.

**The full `mlflow` distribution as a project dependency.** Simpler — the UI
works from the project environment with no second tool. Rejected: it adds a web
framework and its transitive tree to the lockfile that CI and the container
install on every run, to serve a dashboard the pipeline never calls.

## Consequences

**Positive.** Recording an experiment in Sprint 12 is a call against a port that
already exists and is already tested. The vendor is confined to one module and
that confinement is verified by the gate. Switching to SQLite, to a server or to
another tool is configuration, not refactoring. Runs are comparable across
sprints because the key names were fixed before the first run. Nothing in the
pipeline depends on a network service or a credential.

**Negative.** No Model Registry and no model stages while the backend is a file
store; adopting one is a backend migration. No concurrent writers, which is
acceptable for one process and would not be for a team. The run record's
environment evidence is only as good as what the runner passes in — an operator
who forgets `GEO_DECAY_CONTAINER_IMAGE_DIGEST` gets a run without it, and
nothing can detect that from inside. The UI needs a second, isolated
installation, so viewing runs requires network access the first time. `mlflow`
is a dependency with a large transitive surface even in its skinny form, added
in a sprint whose consumer is eight sprints away — accepted because the contract
it anchors is what makes those sprints comparable.

## Amendment 2026-10-27 · The File Store Is in Maintenance Mode

Handoff 011 installed MLflow and three premises of this ADR turned out to be
wrong. All three were found by running the code, and all three are recorded here
rather than quietly corrected.

**1. The file store now requires an explicit opt-in.** MLflow 3.17.2 raises
`MlflowException` when a `FileStore` is constructed: the filesystem tracking
backend "is in maintenance mode and will not receive further updates". The
exception names `MLFLOW_ALLOW_FILE_STORE=true` as the opt-out and
`sqlite:///mlflow.db` as the recommended destination, and points at
`mlflow migrate-filestore` for migrating existing data losslessly. Verified in
`mlflow/store/tracking/file_store.py` in the installed distribution.

**2. `mlflow-skinny` cannot use a database backend at all.** A `sqlite:`
tracking URI fails with `UnsupportedModelRegistryStoreURIException` — the
supported schemes are `['', 'file', 'databricks', 'databricks-uc', 'uc',
'http', 'https']` — and it fails even when only tracking is used and the
registry is never touched. So this ADR's claim that the store is a pure
configuration change is **true for `http(s)` and false for `sqlite`**: moving to
SQLite means changing the distribution too. The architectural payoff is smaller
than claimed, though not absent.

**3. `mlflow-skinny` does carry a web framework.** Version 3.17.2 pulls
`fastapi`, `starlette` and `uvicorn`. The reason given above for choosing skinny
— keeping a web framework out of the lockfile — is therefore false. What skinny
does still avoid is the data-science and database stack, which is the larger
part of the weight and is measured below. The `Delivery frameworks` contract is unaffected: nothing imports
`fastapi`, and import-linter confirms it.

**Decision: stay on the file store, opt in explicitly, and record the migration
as debt with a trigger.**

- **The adapter sets `MLFLOW_ALLOW_FILE_STORE`**, with `setdefault` so an
  operator can override it, and only when the URI it was handed is a `file:`
  one. It is set there and nowhere else because the variable name is an MLflow
  identifier, and the reason this ADR confines MLflow to one module is that
  MLflow identifiers belong in one module. The composition root and the tests
  must not name it. This is not a layer below delivery reading project
  configuration (ADR-006): it is the adapter compensating for a quirk of the
  library it exists to wrap, derived from a value it was given.
- **The alternative is the full `mlflow` distribution with `sqlite:///`**, which
  is the path upstream supports. Rejected for now, on a measurement rather than
  an impression: that environment resolves to **87 packages**, among them
  `scikit-learn`, `scipy`, `pyarrow`, `pandas`, `numpy`, `matplotlib`, `flask`,
  `gunicorn`, `sqlalchemy`, `alembic`, `docker` and `graphene`, none of which
  skinny installs. `scikit-learn` and `scipy` are the decisive entries: they
  would enter the lockfile that CI and the container install **in Sprint 4**,
  and they pin versions that the `torch`/`ultralytics` stack of Block 5 has to
  coexist with. Paying a data-science stack now for a capability first used in
  Sprint 12 is what ADR-007 forbids. By then `numpy` and `pandas` are present
  for other reasons and the trade looks different, which is why the trigger is
  that sprint and not a date.
- **The migration is bounded and tooled**, which is the condition that makes
  deferring legitimate rather than lazy: `mlflow migrate-filestore` is described
  upstream as lossless. The trigger is Sprint 12, the first real experiment.
  Tracked as **MLFLOW-STORE** in [next_tasks.md](../../next_tasks.md).
- `uv.lock` pins 3.17.2, so the backend cannot disappear under the project
  before then. A version bump is the moment to revisit this, not a date.

**The opt-in is a process-level requirement for every reader, not only for the
writer.** The guard is in `FileStore.__init__`, so any process that opens the
store needs `MLFLOW_ALLOW_FILE_STORE=true` in its own environment: the UI, a
notebook, a verification script. Verified by constructing `FileStore` in a
process without the variable, which raises. Only the adapter sets it, and it can
only set it for itself — so every documented command that reads `mlruns/`
carries the variable explicitly. This cost was missed when the decision was
taken and found by handoff 012.

**Migration verified, not assumed.** The claim that a database can be adopted
later *from this architecture* was tested before it was written down. The
adapter delivered by handoff 011, byte for byte unchanged, was executed against
`sqlite:///…` under the full distribution: params, metrics with their `step`,
tags and artifacts all round-trip; `search_registered_models()` responds, so the
Model Registry becomes available; and the artifact root defaults to
`./mlruns/<experiment_id>`, a path already gitignored, so no `.gitignore` change
is needed. The migration is a two-point diff plus a data step, touching neither
the port, nor the adapter, nor the composition root, nor any call site:
`mlflow-skinny` → `mlflow` in `pyproject.toml` with a re-lock; the
`Settings.tracking_uri` default from `file:./mlruns` to
`sqlite:///mlruns/mlflow.db`; and `mlflow migrate-filestore` for the runs
already recorded. This is the port-and-adapter decision above paying for itself,
and it is what makes the deferral legitimate rather than lazy.

**Consequence added.** The Model Registry is unavailable for a second reason
beyond the backend: skinny rejects every registry URI but the file and remote
ones. **Risk accepted:** the project now depends on a backend its vendor has
declared frozen, in exchange for not carrying a dataframe stack eight sprints
early.

## Related

- [ADR-003](adr-003-src-layout-and-layer-boundaries.md) — the layer boundaries
  the port and the adapter respect
- [ADR-005](adr-005-dependency-and-environment-manager.md) — amendment
  2026-10-26, the base image recorded by digest rather than pinned
- [ADR-006](adr-006-logging-strategy.md) — the composition-root precedent, and
  the logging/tracking separation
- [ADR-007](adr-007-mvp-1-0-scope.md) — the reduction this ADR implements
- [Roadmap](../../roadmap.md) — Sprint 4; [Sprint 04 log](../../sprints/sprint-04-mlflow.md)
