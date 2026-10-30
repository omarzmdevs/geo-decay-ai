"""Tracker that records nothing (ADR-008).

:class:`NullTracker` satisfies the experiment-tracking port and does nothing:
no filesystem access, no logging, no third-party import. It has two uses:

- tests that exercise code taking an ``ExperimentTracker`` without recording;
- ``GEO_DECAY_TRACKING_BACKEND=none``, a deliberate run without a record.
"""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path


class NullTracker:
    """Accepts every call of the port and discards it."""

    @contextmanager
    def start_run(
        self, name: str, *, tags: Mapping[str, str] | None = None
    ) -> Iterator[None]:
        """Yield immediately; no run is opened."""
        yield

    def log_params(self, params: Mapping[str, object]) -> None:
        """Discard the params."""

    def log_metrics(
        self, metrics: Mapping[str, float], *, step: int | None = None
    ) -> None:
        """Discard the metrics."""

    def log_artifact(self, path: Path, *, subdir: str | None = None) -> None:
        """Discard the artifact; ``path`` is not read."""
