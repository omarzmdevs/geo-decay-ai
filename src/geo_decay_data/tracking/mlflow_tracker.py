"""MLflow adapter for the experiment-tracking port (ADR-008).

This is the only module in the project allowed to import ``mlflow``; an
import-linter contract enforces it, so the vendor API and its incomplete type
coverage stay contained here. The adapter takes plain values rather than
``Settings``: no layer below delivery reads configuration (ADR-006).

Nothing is caught or retried. A tracking failure must surface, because a silent
one would leave the operator believing an experiment was recorded when it was
not.
"""

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

import mlflow

_FILE_URI_PREFIX = "file:"


class MlflowTracker:
    """Records runs through the MLflow fluent API against ``tracking_uri``.

    For a ``file:`` URI the constructor sets ``MLFLOW_ALLOW_FILE_STORE`` (without
    overriding a value the operator already set). This opts into a backend the
    vendor has declared frozen: MLflow 3.17.2 refuses to open a file store
    otherwise. The decision, its reasoning and the migration trigger are in the
    ADR-008 amendment of 2026-10-27. Any other URI is passed through untouched,
    so its failures remain the vendor's own.
    """

    def __init__(self, tracking_uri: str, experiment: str) -> None:
        if tracking_uri.startswith(_FILE_URI_PREFIX):
            os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment)

    @contextmanager
    def start_run(
        self, name: str, *, tags: Mapping[str, str] | None = None
    ) -> Iterator[None]:
        """Open a run called ``name``; it is closed when the block exits."""
        with mlflow.start_run(run_name=name):
            if tags:
                mlflow.set_tags(dict(tags))
            yield

    def log_params(self, params: Mapping[str, object]) -> None:
        """Record the inputs of the current run."""
        mlflow.log_params(dict(params))

    def log_metrics(
        self, metrics: Mapping[str, float], *, step: int | None = None
    ) -> None:
        """Record measured values of the current run, at ``step`` if given."""
        if step is None:
            mlflow.log_metrics(dict(metrics))
        else:
            mlflow.log_metrics(dict(metrics), step=step)

    def log_artifact(self, path: Path, *, subdir: str | None = None) -> None:
        """Attach the file at ``path`` to the current run, under ``subdir``."""
        mlflow.log_artifact(str(path), artifact_path=subdir)
