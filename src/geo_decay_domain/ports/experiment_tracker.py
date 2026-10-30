"""Experiment-tracking port: how a run is recorded, without saying where.

:class:`ExperimentTracker` declares the four operations the rest of the system
may use to record an experiment:

- ``start_run`` opens a named run as a context manager; everything logged inside
  the ``with`` block belongs to that run, and the run is closed on exit.
- ``log_params`` records the inputs of the run (bounding box, seed, ...).
- ``log_metrics`` records measured values, optionally against a ``step``.
- ``log_artifact`` attaches a file to the run, optionally under a ``subdir``.

A tracker is obtained from the composition root and is never constructed by the
layer that uses it, so the layer depends on this contract and not on any
implementation. Failures are not swallowed: an implementation that cannot
record must raise, because a silent loss would leave the operator believing an
experiment was recorded (ADR-008).

Only the standard library is imported here, so the domain stays pure.
"""

from collections.abc import Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ExperimentTracker(Protocol):
    """Records the parameters, metrics and artifacts of an experiment run."""

    def start_run(
        self, name: str, *, tags: Mapping[str, str] | None = None
    ) -> AbstractContextManager[None]:
        """Open a run called ``name``, optionally labelled with ``tags``."""
        ...

    def log_params(self, params: Mapping[str, object]) -> None:
        """Record the inputs of the current run."""
        ...

    def log_metrics(
        self, metrics: Mapping[str, float], *, step: int | None = None
    ) -> None:
        """Record measured values of the current run, at ``step`` if given."""
        ...

    def log_artifact(self, path: Path, *, subdir: str | None = None) -> None:
        """Attach the file at ``path`` to the current run, under ``subdir``."""
        ...
