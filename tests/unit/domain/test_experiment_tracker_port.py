"""Unit tests for the experiment-tracking port."""

from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path

from geo_decay_domain.ports.experiment_tracker import ExperimentTracker


class _RecordingTracker:
    """Minimal stand-in that satisfies the port structurally."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def start_run(
        self, name: str, *, tags: Mapping[str, str] | None = None
    ) -> AbstractContextManager[None]:
        return self._run(name)

    @contextmanager
    def _run(self, name: str) -> Iterator[None]:
        self.events.append(f"start:{name}")
        yield
        self.events.append(f"end:{name}")

    def log_params(self, params: Mapping[str, object]) -> None:
        self.events.append(f"params:{sorted(params)}")

    def log_metrics(
        self, metrics: Mapping[str, float], *, step: int | None = None
    ) -> None:
        self.events.append(f"metrics:{sorted(metrics)}:{step}")

    def log_artifact(self, path: Path, *, subdir: str | None = None) -> None:
        self.events.append(f"artifact:{path.name}:{subdir}")


def test_a_structural_stub_satisfies_the_port() -> None:
    # The annotation makes strict mypy check the stub against the protocol.
    tracker: ExperimentTracker = _RecordingTracker()

    assert isinstance(tracker, ExperimentTracker)


def test_an_object_missing_a_method_is_not_a_tracker() -> None:
    class _Incomplete:
        def log_params(self, params: Mapping[str, object]) -> None:
            return None

    assert not isinstance(_Incomplete(), ExperimentTracker)


def test_the_port_can_be_driven_through_its_four_operations() -> None:
    stub = _RecordingTracker()
    tracker: ExperimentTracker = stub

    with tracker.start_run("run-a", tags={"k": "v"}):
        tracker.log_params({"seed": 42})
        tracker.log_metrics({"iou": 0.5}, step=1)
        tracker.log_artifact(Path("config.json"), subdir="cfg")

    assert stub.events == [
        "start:run-a",
        "params:['seed']",
        "metrics:['iou']:1",
        "artifact:config.json:cfg",
        "end:run-a",
    ]
