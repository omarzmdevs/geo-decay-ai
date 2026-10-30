"""NullTracker accepts the whole port and touches nothing."""

from pathlib import Path

from geo_decay_data.tracking.null_tracker import NullTracker
from geo_decay_domain.ports.experiment_tracker import ExperimentTracker


def test_null_tracker_is_an_experiment_tracker() -> None:
    assert isinstance(NullTracker(), ExperimentTracker)


def test_null_tracker_accepts_every_call_and_creates_no_path(tmp_path: Path) -> None:
    tracker: ExperimentTracker = NullTracker()
    missing = tmp_path / "never-created"

    with tracker.start_run("nothing", tags={"stage": "test"}):
        tracker.log_params({"a": 1, "b": "two"})
        tracker.log_metrics({"m": 1.0})
        tracker.log_metrics({"m": 2.0}, step=3)
        tracker.log_artifact(missing, subdir="sub")

    assert not missing.exists()
    assert list(tmp_path.iterdir()) == []


def test_null_tracker_run_propagates_exceptions() -> None:
    tracker = NullTracker()
    try:
        with tracker.start_run("failing"):
            raise ValueError("boom")
    except ValueError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("the exception was swallowed")
