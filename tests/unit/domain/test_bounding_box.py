"""Unit tests for ``BoundingBox`` beyond the acceptance contract."""

import math

import pytest

from geo_decay_domain.bounding_box import BoundingBox


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("field", ["min_x", "min_y", "max_x", "max_y"])
def test_non_finite_coordinate_is_rejected_and_named(field: str, bad: float) -> None:
    values = {"min_x": 0.0, "min_y": 0.0, "max_x": 1.0, "max_y": 1.0, field: bad}

    with pytest.raises(ValueError, match=field):
        BoundingBox(**values, crs="EPSG:25830")


def test_surrounding_whitespace_in_crs_is_rejected() -> None:
    with pytest.raises(ValueError, match="crs"):
        BoundingBox(0.0, 0.0, 1.0, 1.0, " EPSG:4326")


def test_ordering_error_reports_both_values() -> None:
    with pytest.raises(ValueError, match=r"min_y=5\.0.*max_y=2\.0"):
        BoundingBox(0.0, 5.0, 1.0, 2.0, "EPSG:4326")


def test_geographic_range_error_reports_limits() -> None:
    with pytest.raises(ValueError, match=r"max_y.*\[-90, 90\].*91"):
        BoundingBox(0.0, 0.0, 1.0, 91.0, "EPSG:4326")
