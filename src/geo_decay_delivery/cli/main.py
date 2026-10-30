"""Command-line entry point of the project (``geo-decay``).

Follows the composition-root pattern of ADR-006 and ADR-008: build
:class:`Settings`, configure logging once, build the tracker, and pass what was
built downwards. The only command today, ``tracking-smoke``, records one run
with the ADR-008 minimum keys to prove that wiring end to end.
"""

import argparse
import json
import logging
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic import ValidationError

from geo_decay_delivery.config import Settings
from geo_decay_delivery.logging_config import configure_logging
from geo_decay_delivery.tracking import build_tracker
from geo_decay_domain.ports.experiment_tracker import ExperimentTracker

logger = logging.getLogger(__name__)

_PROGRAM = "geo-decay"
_SMOKE_COMMAND = "tracking-smoke"
_SMOKE_RUN_NAME = "tracking-smoke"
_CONFIG_ARTIFACT = "config.json"
_DIGEST_TAG = "container_image_digest"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command named in ``argv`` and return the process exit code.

    Returns ``0`` on success and ``2`` when the configuration is invalid, in
    which case the message names the offending variable.
    """
    parser = _build_parser()
    parser.parse_args(argv)

    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as error:
        print(f"{_PROGRAM}: invalid configuration\n{error}", file=sys.stderr)
        return 2

    configure_logging(settings)
    _tracking_smoke(settings, build_tracker(settings))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROGRAM, description="Geo-decay command-line interface."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        _SMOKE_COMMAND,
        help="record one run with the ADR-008 minimum keys to prove the wiring",
    )
    return parser


def _tracking_smoke(settings: Settings, tracker: ExperimentTracker) -> None:
    box = settings.bbox
    tags = (
        {_DIGEST_TAG: settings.container_image_digest}
        if settings.container_image_digest is not None
        else None
    )
    with tracker.start_run(_SMOKE_RUN_NAME, tags=tags):
        tracker.log_params(
            {
                "bbox": f"{box.min_x},{box.min_y},{box.max_x},{box.max_y}",
                "bbox_crs": settings.bbox_crs,
                "random_seed": settings.random_seed,
            }
        )
        tracker.log_metrics({"smoke": 1.0})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / _CONFIG_ARTIFACT
            path.write_text(
                json.dumps(_resolved_config(settings), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            tracker.log_artifact(path)

    if settings.tracking_backend == "none":
        logger.info(
            "Run %r not recorded: the tracking backend is none", _SMOKE_RUN_NAME
        )
    else:
        logger.info(
            "Run %r recorded in experiment %r",
            _SMOKE_RUN_NAME,
            settings.tracking_experiment,
        )


def _resolved_config(settings: Settings) -> dict[str, object]:
    """The settings worth keeping with a run, chosen by allowlist.

    A field added to :class:`Settings` later is not recorded until it is listed
    here, so a secret can never reach ``config.json`` by default (ADR-008).
    """
    box = settings.bbox
    return {
        "bbox": [box.min_x, box.min_y, box.max_x, box.max_y],
        "bbox_crs": settings.bbox_crs,
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "data_dir": str(settings.data_dir),
        "random_seed": settings.random_seed,
        "tracking_backend": settings.tracking_backend,
        "tracking_uri": _without_credentials(settings.tracking_uri),
        "tracking_experiment": settings.tracking_experiment,
        "container_image_digest": settings.container_image_digest,
    }


def _without_credentials(uri: str) -> str:
    """Drop any ``user:password@`` part of a URI before it is recorded."""
    parts = urlsplit(uri)
    if "@" not in parts.netloc:
        return uri
    return urlunsplit(parts._replace(netloc=parts.netloc.rsplit("@", 1)[1]))


if __name__ == "__main__":
    raise SystemExit(main())
