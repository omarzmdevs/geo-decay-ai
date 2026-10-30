"""Tracker composition (ADR-008).

:func:`build_tracker` is called once by each delivery entry point, right after
:func:`geo_decay_delivery.logging_config.configure_logging`, and the tracker it
returns is passed downwards. The return type is the domain port, so no caller
can depend on which implementation it got.
"""

import logging

from geo_decay_data.tracking.mlflow_tracker import MlflowTracker
from geo_decay_data.tracking.null_tracker import NullTracker
from geo_decay_delivery.config import Settings
from geo_decay_domain.ports.experiment_tracker import ExperimentTracker

logger = logging.getLogger(__name__)


def build_tracker(settings: Settings) -> ExperimentTracker:
    """Build the experiment tracker selected by ``settings.tracking_backend``.

    ``mlflow`` records runs in the configured store; ``none`` selects a tracker
    that discards everything. The choice is logged at INFO, because an operator
    who believes a run is being recorded while the backend is ``none`` is the
    one failure this composition can introduce.
    """
    match settings.tracking_backend:
        case "mlflow":
            logger.info(
                "Experiment tracking: mlflow, experiment %r",
                settings.tracking_experiment,
            )
            return MlflowTracker(settings.tracking_uri, settings.tracking_experiment)
        case "none":
            logger.info("Experiment tracking: none, runs are not recorded")
            return NullTracker()
