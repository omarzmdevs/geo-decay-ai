"""MlflowTracker records runs into a real file store under ``tmp_path``."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from mlflow.entities import Run
from mlflow.tracking import MlflowClient
from mlflow.tracking.registry import UnsupportedModelRegistryStoreURIException

from geo_decay_data.tracking.mlflow_tracker import MlflowTracker
from geo_decay_domain.ports.experiment_tracker import ExperimentTracker

EXPERIMENT = "unit-test-experiment"


@pytest.fixture
def store(tmp_path: Path) -> str:
    return f"file:{tmp_path / 'runs'}"


def _only_run(store: str) -> tuple[MlflowClient, Run]:
    client = MlflowClient(tracking_uri=store)
    experiment = client.get_experiment_by_name(EXPERIMENT)
    assert experiment is not None
    runs = client.search_runs([experiment.experiment_id])
    assert len(runs) == 1
    return client, runs[0]


def test_mlflow_tracker_is_an_experiment_tracker(store: str) -> None:
    assert isinstance(MlflowTracker(store, EXPERIMENT), ExperimentTracker)


def test_run_appears_under_the_configured_experiment(store: str) -> None:
    tracker = MlflowTracker(store, EXPERIMENT)

    with tracker.start_run("smoke"):
        pass

    _, run = _only_run(store)
    assert run.info.run_name == "smoke"
    assert run.info.status == "FINISHED"


def test_params_and_tags_round_trip(store: str) -> None:
    tracker = MlflowTracker(store, EXPERIMENT)

    with tracker.start_run("smoke", tags={"stage": "test"}):
        tracker.log_params({"a": 1, "b": "two"})

    _, run = _only_run(store)
    assert run.data.params == {"a": "1", "b": "two"}
    assert run.data.tags["stage"] == "test"


def test_metrics_round_trip_and_step_reaches_the_history(store: str) -> None:
    tracker = MlflowTracker(store, EXPERIMENT)

    with tracker.start_run("smoke"):
        tracker.log_metrics({"m": 0.5})
        tracker.log_metrics({"m": 0.25}, step=1)

    client, run = _only_run(store)
    history = client.get_metric_history(run.info.run_id, "m")
    assert {(m.step, m.value) for m in history} == {(0, 0.5), (1, 0.25)}


def test_artifact_is_stored_at_the_root_and_under_a_subdir(
    store: str, tmp_path: Path
) -> None:
    tracker = MlflowTracker(store, EXPERIMENT)
    note = tmp_path / "note.txt"
    note.write_text("hello")

    with tracker.start_run("smoke"):
        tracker.log_artifact(note)
        tracker.log_artifact(note, subdir="extra")

    client, run = _only_run(store)
    assert "note.txt" in [f.path for f in client.list_artifacts(run.info.run_id)]
    nested = client.list_artifacts(run.info.run_id, "extra")
    assert [f.path for f in nested] == ["extra/note.txt"]


def test_tracking_failures_are_not_swallowed(store: str, tmp_path: Path) -> None:
    tracker = MlflowTracker(store, EXPERIMENT)

    with pytest.raises(FileNotFoundError, match="missing.txt"):
        with tracker.start_run("smoke"):
            tracker.log_artifact(tmp_path / "missing.txt")


def test_file_store_works_without_the_operator_opting_in(store: str) -> None:
    # A fresh interpreter with every MLflow setting removed from its environment
    # stands in for a process where the file-store opt-in was never set.
    env = {k: v for k, v in os.environ.items() if not k.startswith("MLFLOW_")}
    script = (
        "import sys\n"
        "from mlflow.tracking import MlflowClient\n"
        "from geo_decay_data.tracking.mlflow_tracker import MlflowTracker\n"
        "uri, name = sys.argv[1:]\n"
        "with MlflowTracker(uri, name).start_run('smoke'):\n"
        "    pass\n"
        "client = MlflowClient(tracking_uri=uri)\n"
        "experiment = client.get_experiment_by_name(name)\n"
        "assert experiment is not None\n"
        "runs = client.search_runs([experiment.experiment_id])\n"
        "print([r.info.run_name for r in runs])\n"
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, store, EXPERIMENT],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("['smoke']")


def test_a_non_file_uri_fails_with_the_vendor_error(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedModelRegistryStoreURIException):
        MlflowTracker(f"sqlite:///{tmp_path / 'mlflow.db'}", EXPERIMENT)
