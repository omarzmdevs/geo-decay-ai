"""``geo-decay tracking-smoke`` end to end against a real file store."""

import json
from pathlib import Path

import pytest
from mlflow.entities import Run
from mlflow.tracking import MlflowClient

from geo_decay_delivery.cli.main import _without_credentials, main

EXPERIMENT = "cli-test"
_VARIABLES = (
    "GEO_DECAY_BBOX",
    "GEO_DECAY_BBOX_CRS",
    "GEO_DECAY_LOG_LEVEL",
    "GEO_DECAY_LOG_FORMAT",
    "GEO_DECAY_DATA_DIR",
    "GEO_DECAY_RANDOM_SEED",
    "GEO_DECAY_TRACKING_BACKEND",
    "GEO_DECAY_TRACKING_URI",
    "GEO_DECAY_TRACKING_EXPERIMENT",
    "GEO_DECAY_CONTAINER_IMAGE_DIGEST",
)


@pytest.fixture(autouse=True)
def environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Empty working directory, a throwaway extent and a store under ``tmp_path``."""
    monkeypatch.chdir(tmp_path)
    for name in _VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GEO_DECAY_BBOX", "0,0,1,1")
    monkeypatch.setenv("GEO_DECAY_BBOX_CRS", "EPSG:4326")
    monkeypatch.setenv("GEO_DECAY_TRACKING_URI", f"file:{tmp_path / 'runs'}")
    monkeypatch.setenv("GEO_DECAY_TRACKING_EXPERIMENT", EXPERIMENT)


def _only_run(tmp_path: Path) -> tuple[MlflowClient, Run]:
    client = MlflowClient(tracking_uri=f"file:{tmp_path / 'runs'}")
    experiment = client.get_experiment_by_name(EXPERIMENT)
    assert experiment is not None
    runs = client.search_runs([experiment.experiment_id])
    assert len(runs) == 1
    return client, runs[0]


def test_smoke_records_params_metric_and_config_artifact(tmp_path: Path) -> None:
    assert main(["tracking-smoke"]) == 0

    client, run = _only_run(tmp_path)
    assert run.info.run_name == "tracking-smoke"
    assert run.data.params == {
        "bbox": "0.0,0.0,1.0,1.0",
        "bbox_crs": "EPSG:4326",
        "random_seed": "42",
    }
    assert run.data.metrics["smoke"] == 1.0
    artifacts = [item.path for item in client.list_artifacts(run.info.run_id)]
    assert "config.json" in artifacts


def test_digest_is_recorded_as_a_tag_when_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEO_DECAY_CONTAINER_IMAGE_DIGEST", "sha256:feedface")

    assert main(["tracking-smoke"]) == 0

    _, run = _only_run(tmp_path)
    assert run.data.tags["container_image_digest"] == "sha256:feedface"


def test_digest_tag_is_absent_when_not_set(tmp_path: Path) -> None:
    assert main(["tracking-smoke"]) == 0

    _, run = _only_run(tmp_path)
    assert "container_image_digest" not in run.data.tags


def test_config_artifact_carries_no_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SOME_API_KEY", "hunter2-key-value")
    monkeypatch.setenv("SOME_PASSWORD", "hunter2-password-value")

    assert main(["tracking-smoke"]) == 0

    client, run = _only_run(tmp_path)
    local = Path(client.download_artifacts(run.info.run_id, "config.json"))
    body = local.read_text(encoding="utf-8")
    assert "hunter2" not in body
    resolved = json.loads(body)
    assert resolved["bbox_crs"] == "EPSG:4326"
    assert resolved["tracking_experiment"] == EXPERIMENT


def test_credentials_in_the_tracking_uri_are_not_recorded() -> None:
    assert (
        _without_credentials("https://user:s3cret@tracking.example/path")
        == "https://tracking.example/path"
    )
    assert _without_credentials("file:./mlruns") == "file:./mlruns"


def test_none_backend_succeeds_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEO_DECAY_TRACKING_BACKEND", "none")

    assert main(["tracking-smoke"]) == 0

    assert not (tmp_path / "runs").exists()


def test_missing_bbox_returns_2_and_names_the_variable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GEO_DECAY_BBOX")

    assert main(["tracking-smoke"]) == 2

    assert "GEO_DECAY_BBOX" in capsys.readouterr().err


def test_help_exits_0_and_names_the_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--help"])

    assert raised.value.code == 0
    assert "tracking-smoke" in capsys.readouterr().out
