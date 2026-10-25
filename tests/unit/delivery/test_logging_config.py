"""Unit tests for ``configure_logging``: one stream, one format, set at start-up."""

import json
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from geo_decay_delivery.config import Settings
from geo_decay_delivery.logging_config import configure_logging


@pytest.fixture(autouse=True)
def isolated_logging(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Run in an empty directory and restore the global logging state afterwards.

    ``configure_logging`` changes the root logger and the level of third-party
    loggers for the whole process, so each test puts them back.
    """
    monkeypatch.delenv("GEO_DECAY_LOG_LEVEL", raising=False)
    monkeypatch.delenv("GEO_DECAY_LOG_FORMAT", raising=False)
    monkeypatch.setenv("GEO_DECAY_BBOX", "10,20,30,40")
    monkeypatch.setenv("GEO_DECAY_BBOX_CRS", "EPSG:25830")
    monkeypatch.chdir(tmp_path)

    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    yield
    root.handlers[:] = saved_handlers
    root.setLevel(saved_level)
    logging.getLogger("urllib3").setLevel(logging.NOTSET)


def _configure(
    monkeypatch: pytest.MonkeyPatch, log_format: str, log_level: str = "INFO"
) -> None:
    monkeypatch.setenv("GEO_DECAY_LOG_FORMAT", log_format)
    monkeypatch.setenv("GEO_DECAY_LOG_LEVEL", log_level)
    # bbox and bbox_crs are filled from the environment; mypy only sees the
    # synthesised __init__ that lists them as required.
    configure_logging(Settings())  # type: ignore[call-arg]


def test_json_format_writes_one_parseable_line_per_record(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure(monkeypatch, "json")

    logging.getLogger("x").info("hello")

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["level"] == "INFO"
    assert record["logger"] == "x"
    assert record["message"] == "hello"
    assert "timestamp" in record


def test_json_format_carries_the_exception_text(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure(monkeypatch, "json")

    try:
        raise ValueError("bad tile")
    except ValueError:
        logging.getLogger("x").exception("failed")

    record = json.loads(capsys.readouterr().out.splitlines()[0])
    assert record["level"] == "ERROR"
    assert "ValueError: bad tile" in record["exception"]


def test_text_format_is_not_json_and_names_logger_and_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure(monkeypatch, "text")

    logging.getLogger("x").info("hello")

    out = capsys.readouterr().out
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)
    assert " INFO x hello" in out


def test_root_level_follows_the_settings(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure(monkeypatch, "text", log_level="WARNING")

    logging.getLogger("x").info("quiet")
    logging.getLogger("x").warning("loud")

    assert logging.getLogger().level == logging.WARNING
    out = capsys.readouterr().out
    assert "quiet" not in out
    assert "loud" in out


def test_noisy_third_party_loggers_are_held_at_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(monkeypatch, "text", log_level="DEBUG")

    assert logging.getLogger().level == logging.DEBUG
    assert logging.getLogger("urllib3").getEffectiveLevel() >= logging.WARNING


def test_loggers_created_before_configuration_keep_working(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    early = logging.getLogger("library.imported_early")

    _configure(monkeypatch, "text")
    early.warning("still here")

    assert early.disabled is False
    assert "still here" in capsys.readouterr().out


def test_calling_twice_leaves_exactly_one_root_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(monkeypatch, "json")
    _configure(monkeypatch, "json")

    assert len(logging.getLogger().handlers) == 1


def test_records_go_to_standard_output_and_no_file_handler_is_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(monkeypatch, "text")

    (handler,) = logging.getLogger().handlers
    assert isinstance(handler, logging.StreamHandler)
    assert not isinstance(handler, logging.FileHandler)
    assert handler.stream is sys.stdout
