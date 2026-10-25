"""Start-up logging configuration (ADR-006).

Each delivery entry point calls :func:`configure_logging` once, with the
:class:`Settings` it has already built. Every other module logs through
``logging.getLogger(__name__)`` from the standard library and never imports
this one, so the call sites stay independent of the configuration.
"""

import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any

from geo_decay_delivery.config import Settings

_TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

# Third-party loggers held at WARNING whatever the root level is. Later sprints
# extend this map as new noisy libraries appear.
_NOISY_LOGGER_LEVELS: dict[str, str] = {
    "urllib3": "WARNING",
    "botocore": "WARNING",
    "matplotlib": "WARNING",
    "PIL": "WARNING",
}


class JsonFormatter(logging.Formatter):
    """Formats each record as one JSON object on a single line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Apply the logging configuration built from ``settings``.

    Safe to call more than once: ``dictConfig`` replaces the handlers it
    installed on the root logger earlier instead of adding new ones.
    """
    logging.config.dictConfig(_build_config(settings))


def _build_config(settings: Settings) -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "text": {"format": _TEXT_FORMAT},
            "json": {"()": JsonFormatter},
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": settings.log_format,
            },
        },
        "root": {"level": settings.log_level, "handlers": ["stdout"]},
        "loggers": {
            name: {"level": level} for name, level in _NOISY_LOGGER_LEVELS.items()
        },
    }
