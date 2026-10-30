"""``build_tracker`` selects the adapter named by the settings."""

import logging
from pathlib import Path

import pytest

from geo_decay_data.tracking.mlflow_tracker import MlflowTracker
from geo_decay_data.tracking.null_tracker import NullTracker
from geo_decay_delivery.config import Settings
from geo_decay_delivery.tracking import build_tracker
from geo_decay_domain.bounding_box import BoundingBox
from geo_decay_domain.ports.experiment_tracker import ExperimentTracker


def _settings(tmp_path: Path, backend: str) -> Settings:
    return Settings.model_validate(
        {
            "GEO_DECAY_BBOX_CRS": "EPSG:4326",
            "GEO_DECAY_BBOX": BoundingBox(0, 0, 1, 1, "EPSG:4326"),
            "GEO_DECAY_TRACKING_BACKEND": backend,
            "GEO_DECAY_TRACKING_URI": f"file:{tmp_path / 'runs'}",
            "GEO_DECAY_TRACKING_EXPERIMENT": "unit-test",
        }
    )


def test_mlflow_backend_returns_the_mlflow_adapter(tmp_path: Path) -> None:
    tracker: ExperimentTracker = build_tracker(_settings(tmp_path, "mlflow"))

    assert isinstance(tracker, MlflowTracker)


def test_none_backend_returns_the_null_adapter(tmp_path: Path) -> None:
    tracker: ExperimentTracker = build_tracker(_settings(tmp_path, "none"))

    assert isinstance(tracker, NullTracker)


@pytest.mark.parametrize("backend", ["mlflow", "none"])
def test_selected_backend_is_logged_at_info(
    tmp_path: Path, backend: str, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="geo_decay_delivery.tracking"):
        build_tracker(_settings(tmp_path, backend))

    assert any(
        record.levelno == logging.INFO and backend in record.getMessage()
        for record in caplog.records
    )


def test_none_backend_writes_nothing(tmp_path: Path) -> None:
    build_tracker(_settings(tmp_path, "none"))

    assert not (tmp_path / "runs").exists()
