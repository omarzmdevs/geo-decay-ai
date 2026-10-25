"""Acceptance tests for ``geo_decay_domain.bounding_box.BoundingBox`` (handoff 007).

Written from the handoff's Specification only. The bounding box is a data
contract: a swapped axis or an unchecked extent gives results that look
plausible and are wrong, so each rule below is pinned individually.
"""

import dataclasses

import pytest

from geo_decay_domain.bounding_box import BoundingBox

MADRID = (-3.7, 40.4, -3.6, 40.5)


# --- Axis order: x first, then y ------------------------------------------------


def test_positional_arguments_are_min_x_min_y_max_x_max_y_crs() -> None:
    box = BoundingBox(-3.7, 40.4, -3.6, 40.5, "EPSG:4326")

    assert box.min_x == -3.7
    assert box.min_y == 40.4
    assert box.max_x == -3.6
    assert box.max_y == 40.5
    assert box.crs == "EPSG:4326"


def test_field_order_is_x_then_y_then_crs() -> None:
    names = [field.name for field in dataclasses.fields(BoundingBox)]

    assert names == ["min_x", "min_y", "max_x", "max_y", "crs"]


def test_keyword_arguments_are_accepted() -> None:
    box = BoundingBox(min_x=1.0, min_y=2.0, max_x=3.0, max_y=4.0, crs="EPSG:4326")

    assert (box.min_x, box.min_y, box.max_x, box.max_y) == (1.0, 2.0, 3.0, 4.0)


def test_extent_asymmetric_in_x_and_y_is_not_transposed() -> None:
    # Wide in x (20 units), narrow in y (2 units): a transposed reading would
    # swap these two extents.
    box = BoundingBox(0.0, 10.0, 20.0, 12.0, "EPSG:4326")

    assert box.max_x - box.min_x == 20.0
    assert box.max_y - box.min_y == 2.0


# --- Strict ordering on both axes -----------------------------------------------


@pytest.mark.parametrize(
    ("min_x", "min_y", "max_x", "max_y"),
    [
        (1.0, 0.0, 0.0, 1.0),  # min_x > max_x
        (0.0, 1.0, 1.0, 0.0),  # min_y > max_y
        (1.0, 1.0, 0.0, 0.0),  # both reversed
    ],
    ids=["x-reversed", "y-reversed", "both-reversed"],
)
def test_reversed_axis_is_rejected(
    min_x: float, min_y: float, max_x: float, max_y: float
) -> None:
    with pytest.raises(ValueError):
        BoundingBox(min_x, min_y, max_x, max_y, "EPSG:4326")


@pytest.mark.parametrize(
    ("min_x", "min_y", "max_x", "max_y"),
    [
        (1.0, 0.0, 1.0, 1.0),  # min_x == max_x
        (0.0, 1.0, 1.0, 1.0),  # min_y == max_y
        (1.0, 1.0, 1.0, 1.0),  # a point
    ],
    ids=["zero-width", "zero-height", "point"],
)
def test_degenerate_box_is_rejected(
    min_x: float, min_y: float, max_x: float, max_y: float
) -> None:
    with pytest.raises(ValueError):
        BoundingBox(min_x, min_y, max_x, max_y, "EPSG:4326")


def test_degenerate_box_is_rejected_for_projected_crs_too() -> None:
    with pytest.raises(ValueError):
        BoundingBox(500000.0, 4470000.0, 500000.0, 4480000.0, "EPSG:25830")


def test_ordering_error_names_an_offending_field_and_the_value() -> None:
    with pytest.raises(ValueError) as excinfo:
        BoundingBox(7.5, 0.0, 2.5, 1.0, "EPSG:4326")

    message = str(excinfo.value)
    assert "min_x" in message or "max_x" in message
    assert "7.5" in message or "2.5" in message


# --- CRS: required, non-empty, normalised, AUTHORITY:CODE -----------------------


@pytest.mark.parametrize(
    "crs",
    [
        "",
        "4326",
        "EPSG",
        "EPSG:",
        ":4326",
        "EPSG 4326",
        "EPSG-4326",
        "EPSG:43 26",
        "EPSG:4326:1",
    ],
)
def test_malformed_crs_is_rejected(crs: str) -> None:
    with pytest.raises(ValueError):
        BoundingBox(*MADRID, crs)


def test_crs_is_required() -> None:
    with pytest.raises(TypeError):
        BoundingBox(*MADRID)  # type: ignore[call-arg]


def test_crs_error_names_the_field_and_the_value() -> None:
    with pytest.raises(ValueError) as excinfo:
        BoundingBox(*MADRID, "4326")

    message = str(excinfo.value)
    assert "crs" in message
    assert "4326" in message


def test_empty_crs_error_names_the_field() -> None:
    with pytest.raises(ValueError) as excinfo:
        BoundingBox(*MADRID, "")

    assert "crs" in str(excinfo.value)


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("epsg:4326", "EPSG:4326"),
        ("Epsg:4326", "EPSG:4326"),
        ("EPSG:4326", "EPSG:4326"),
        ("epsg:25830", "EPSG:25830"),
        ("esri:54009", "ESRI:54009"),
    ],
)
def test_crs_is_normalised_to_upper_case(given: str, expected: str) -> None:
    # Coordinates valid under every CRS above, so only the CRS is under test.
    box = BoundingBox(1.0, 2.0, 3.0, 4.0, given)

    assert box.crs == expected


# --- EPSG:4326 range check ------------------------------------------------------


def test_valid_geographic_box_is_accepted() -> None:
    BoundingBox(*MADRID, "EPSG:4326")


def test_geographic_limits_are_inclusive() -> None:
    box = BoundingBox(-180.0, -90.0, 180.0, 90.0, "EPSG:4326")

    assert (box.min_x, box.min_y, box.max_x, box.max_y) == (-180.0, -90.0, 180.0, 90.0)


@pytest.mark.parametrize(
    ("args", "field", "value"),
    [
        ((-181.0, 0.0, 1.0, 1.0), "min_x", "-181"),
        ((0.0, 0.0, 181.0, 1.0), "max_x", "181"),
        ((0.0, -91.0, 1.0, 1.0), "min_y", "-91"),
        ((0.0, 0.0, 1.0, 91.0), "max_y", "91"),
    ],
    ids=["min_x-below", "max_x-above", "min_y-below", "max_y-above"],
)
def test_out_of_range_geographic_value_is_rejected_and_named(
    args: tuple[float, float, float, float], field: str, value: str
) -> None:
    with pytest.raises(ValueError) as excinfo:
        BoundingBox(*args, "EPSG:4326")

    message = str(excinfo.value)
    assert field in message
    assert value in message


def test_range_check_applies_after_crs_normalisation() -> None:
    with pytest.raises(ValueError):
        BoundingBox(-181.0, 0.0, 1.0, 1.0, "epsg:4326")


def test_swapped_latitude_longitude_is_caught_for_geographic_crs() -> None:
    # Tokyo written latitude-first: longitude 139.6 lands in the y slot, which
    # is beyond 90 degrees and must be rejected.
    with pytest.raises(ValueError):
        BoundingBox(35.6, 139.6, 35.7, 139.8, "EPSG:4326")


# --- Projected CRS: no range check ----------------------------------------------


@pytest.mark.parametrize(
    ("args", "crs"),
    [
        ((500000.0, 4470000.0, 510000.0, 4480000.0), "EPSG:25830"),
        ((-20037508.34, -20048966.10, 20037508.34, 20048966.10), "EPSG:3857"),
        ((181.0, 91.0, 1000.0, 5000.0), "EPSG:3857"),
        ((-1000.0, -1000.0, 1000.0, 1000.0), "EPSG:32630"),
        ((200.0, 100.0, 300.0, 200.0), "ESRI:54009"),
    ],
)
def test_values_outside_geographic_range_are_accepted_for_other_crs(
    args: tuple[float, float, float, float], crs: str
) -> None:
    box = BoundingBox(*args, crs)

    assert (box.min_x, box.min_y, box.max_x, box.max_y) == args
    assert box.crs == crs


# --- Immutability ---------------------------------------------------------------


@pytest.mark.parametrize("field", ["min_x", "min_y", "max_x", "max_y", "crs"])
def test_fields_cannot_be_reassigned(field: str) -> None:
    box = BoundingBox(*MADRID, "EPSG:4326")
    original = getattr(box, field)

    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(box, field, "EPSG:3857" if field == "crs" else 0.0)

    assert getattr(box, field) == original


def test_attributes_cannot_be_added() -> None:
    box = BoundingBox(*MADRID, "EPSG:4326")

    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        box.extra = 1  # type: ignore[attr-defined]


def test_fields_cannot_be_deleted() -> None:
    box = BoundingBox(*MADRID, "EPSG:4326")

    with pytest.raises(dataclasses.FrozenInstanceError):
        delattr(box, "min_x")


def test_equal_values_compare_equal_and_hash_equal() -> None:
    a = BoundingBox(*MADRID, "EPSG:4326")
    b = BoundingBox(*MADRID, "epsg:4326")

    assert a == b
    assert hash(a) == hash(b)
