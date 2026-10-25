"""Typed, validated runtime configuration.

Every setting is read from the environment (prefix ``GEO_DECAY_``) or from a
``.env`` file, and validated when :class:`Settings` is constructed. Nothing is
read at import time and there is no module-level instance: the caller builds
``Settings()`` explicitly at start-up and passes it down.

Each field is bound to its full environment variable name, so a validation
error names the variable that is wrong.
"""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from geo_decay_domain.bounding_box import BoundingBox

_BBOX_VAR = "GEO_DECAY_BBOX"
_BBOX_CRS_VAR = "GEO_DECAY_BBOX_CRS"

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["text", "json"]


class Settings(BaseSettings):
    """Runtime configuration of the project.

    ``GEO_DECAY_BBOX_CRS`` and ``GEO_DECAY_BBOX`` are required and have no
    default: the working CRS is not decided here (ADR-004).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    bbox_crs: str = Field(
        validation_alias=_BBOX_CRS_VAR,
        description="Authority code the bounding box is expressed in, e.g. EPSG:4326.",
    )
    bbox: Annotated[BoundingBox, NoDecode] = Field(
        validation_alias=_BBOX_VAR,
        description="Target extent as 'min_x,min_y,max_x,max_y' (x first, then y).",
    )
    log_level: LogLevel = Field(default="INFO", validation_alias="GEO_DECAY_LOG_LEVEL")
    log_format: LogFormat = Field(
        default="text", validation_alias="GEO_DECAY_LOG_FORMAT"
    )
    data_dir: Path = Field(default=Path("data"), validation_alias="GEO_DECAY_DATA_DIR")
    random_seed: int = Field(default=42, validation_alias="GEO_DECAY_RANDOM_SEED")

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("log_format", mode="before")
    @classmethod
    def _lower_log_format(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("bbox", mode="before")
    @classmethod
    def _parse_bbox(cls, value: object, info: ValidationInfo) -> BoundingBox:
        if isinstance(value, BoundingBox):
            return value
        crs = info.data.get("bbox_crs")
        if not isinstance(crs, str):
            raise ValueError(
                f"{_BBOX_VAR} cannot be checked without a valid {_BBOX_CRS_VAR}"
            )
        expected = (
            f"{_BBOX_VAR} must be four comma-separated numbers "
            "'min_x,min_y,max_x,max_y'"
        )
        if not isinstance(value, str):
            raise ValueError(f"{expected}, got {value!r}")
        try:
            min_x, min_y, max_x, max_y = (float(part) for part in value.split(","))
        except ValueError:
            raise ValueError(f"{expected}, got {value!r}") from None
        try:
            return BoundingBox(min_x, min_y, max_x, max_y, crs)
        except ValueError as error:
            raise ValueError(
                f"{_BBOX_VAR} with {_BBOX_CRS_VAR}={crs!r}: {error}"
            ) from None
