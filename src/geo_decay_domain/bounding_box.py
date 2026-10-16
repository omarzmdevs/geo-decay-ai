"""Bounding box value object: the system's unit of work."""

import math
import re
from dataclasses import dataclass

_CRS_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*:[A-Z0-9_]+")
_GEOGRAPHIC_CRS = "EPSG:4326"
_LONGITUDE_RANGE = (-180.0, 180.0)
_LATITUDE_RANGE = (-90.0, 90.0)


@dataclass(frozen=True)
class BoundingBox:
    """A rectangular extent expressed in one coordinate reference system.

    Axis order is **x first, then y**: longitude/easting before
    latitude/northing, whatever the CRS declares in its own axis order. The
    fields follow it: ``min_x, min_y, max_x, max_y``.

    ``crs`` is an ``AUTHORITY:CODE`` string such as ``EPSG:4326``, normalised to
    upper case. Both axes must be strictly ordered (``min < max``): a degenerate
    box is an error, not an empty result. For ``EPSG:4326`` the coordinates must
    also be valid longitudes and latitudes; no range check is applied to any
    other CRS, because the valid range depends on the projection.

    Raises:
        ValueError: if any coordinate is not finite, the axes are not strictly
            ordered, the CRS is malformed, or a ``EPSG:4326`` coordinate is out
            of range. The message names the offending field and the value.
    """

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    crs: str

    def __post_init__(self) -> None:
        for name in ("min_x", "min_y", "max_x", "max_y"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"{name} must be a finite number, got {value!r}")

        crs = self.crs.upper()
        if not _CRS_PATTERN.fullmatch(crs):
            raise ValueError(
                f"crs must be non-empty and of the form AUTHORITY:CODE "
                f"(for example EPSG:4326), got {self.crs!r}"
            )
        object.__setattr__(self, "crs", crs)

        if self.min_x >= self.max_x:
            raise ValueError(
                f"min_x must be less than max_x, got min_x={self.min_x!r} "
                f"and max_x={self.max_x!r}"
            )
        if self.min_y >= self.max_y:
            raise ValueError(
                f"min_y must be less than max_y, got min_y={self.min_y!r} "
                f"and max_y={self.max_y!r}"
            )

        if crs == _GEOGRAPHIC_CRS:
            self._check_range("min_x", _LONGITUDE_RANGE)
            self._check_range("max_x", _LONGITUDE_RANGE)
            self._check_range("min_y", _LATITUDE_RANGE)
            self._check_range("max_y", _LATITUDE_RANGE)

    def _check_range(self, name: str, bounds: tuple[float, float]) -> None:
        value: float = getattr(self, name)
        low, high = bounds
        if not low <= value <= high:
            raise ValueError(
                f"{name} must be within [{low:g}, {high:g}] for "
                f"{_GEOGRAPHIC_CRS}, got {value!r}"
            )
