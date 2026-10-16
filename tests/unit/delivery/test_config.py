"""Unit tests for ``Settings``: typed, validated, start-up configuration."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from geo_decay_delivery import config
from geo_decay_delivery.config import Settings
from geo_decay_domain.bounding_box import BoundingBox

_VARIABLES = (
    "GEO_DECAY_BBOX",
    "GEO_DECAY_BBOX_CRS",
    "GEO_DECAY_LOG_LEVEL",
    "GEO_DECAY_LOG_FORMAT",
    "GEO_DECAY_DATA_DIR",
    "GEO_DECAY_RANDOM_SEED",
)


def _load_settings() -> Settings:
    # bbox and bbox_crs are filled from the environment, not from arguments;
    # mypy only sees the synthesised __init__ that lists them as required.
    return Settings()  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run in an empty directory with no ``GEO_DECAY_*`` variable set.

    ``Settings`` also reads ``.env`` from the working directory, so a developer's
    own file must not leak into the tests.
    """
    for name in _VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def valid_bbox(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX", "10,20,30,40")
    monkeypatch.setenv("GEO_DECAY_BBOX_CRS", "EPSG:25830")


@pytest.mark.usefixtures("valid_bbox")
def test_valid_bbox_is_exposed_as_a_bounding_box_in_x_first_order() -> None:
    settings = _load_settings()

    assert settings.bbox == BoundingBox(10.0, 20.0, 30.0, 40.0, "EPSG:25830")


@pytest.mark.usefixtures("valid_bbox")
def test_whitespace_around_bbox_numbers_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX", " 10, 20 ,30 , 40 ")

    assert _load_settings().bbox == BoundingBox(10.0, 20.0, 30.0, 40.0, "EPSG:25830")


@pytest.mark.usefixtures("valid_bbox")
def test_crs_is_normalised_to_upper_case(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX_CRS", "epsg:25830")

    assert _load_settings().bbox.crs == "EPSG:25830"


@pytest.mark.usefixtures("valid_bbox")
def test_optional_settings_have_defaults() -> None:
    settings = _load_settings()

    assert settings.log_level == "INFO"
    assert settings.log_format == "text"
    assert settings.data_dir == Path("data")
    assert settings.random_seed == 42


@pytest.mark.usefixtures("valid_bbox")
def test_optional_settings_are_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEO_DECAY_LOG_LEVEL", "debug")
    monkeypatch.setenv("GEO_DECAY_LOG_FORMAT", "JSON")
    monkeypatch.setenv("GEO_DECAY_DATA_DIR", "somewhere/else")
    monkeypatch.setenv("GEO_DECAY_RANDOM_SEED", "7")

    settings = _load_settings()

    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"
    assert settings.data_dir == Path("somewhere/else")
    assert settings.random_seed == 7


def test_settings_are_read_from_a_dotenv_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "GEO_DECAY_BBOX=1,2,3,4\nGEO_DECAY_BBOX_CRS=EPSG:25830\n"
        "GEO_DECAY_RANDOM_SEED=11\n"
    )

    settings = _load_settings()

    assert settings.bbox == BoundingBox(1.0, 2.0, 3.0, 4.0, "EPSG:25830")
    assert settings.random_seed == 11


def test_environment_takes_precedence_over_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env").write_text(
        "GEO_DECAY_BBOX=1,2,3,4\nGEO_DECAY_BBOX_CRS=EPSG:25830\n"
    )
    monkeypatch.setenv("GEO_DECAY_BBOX", "5,6,7,8")

    assert _load_settings().bbox == BoundingBox(5.0, 6.0, 7.0, 8.0, "EPSG:25830")


@pytest.mark.usefixtures("valid_bbox")
@pytest.mark.parametrize("bad", ["1,2,3", "1,2,3,4,5", "a,b,c,d", "1;2;3;4", ""])
def test_malformed_bbox_raises_and_names_the_variable(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX", bad)

    with pytest.raises(ValidationError, match="GEO_DECAY_BBOX"):
        _load_settings()


@pytest.mark.usefixtures("valid_bbox")
def test_malformed_bbox_message_shows_the_value_received(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX", "1,2,3")

    with pytest.raises(ValidationError, match=r"got '1,2,3'"):
        _load_settings()


@pytest.mark.usefixtures("valid_bbox")
@pytest.mark.parametrize(
    ("bbox", "field"),
    [("30,20,10,40", "min_x"), ("10,40,30,20", "min_y")],
)
def test_misordered_bbox_names_the_variable_and_the_axis(
    monkeypatch: pytest.MonkeyPatch, bbox: str, field: str
) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX", bbox)

    with pytest.raises(ValidationError, match=rf"GEO_DECAY_BBOX.*{field}"):
        _load_settings()


def test_geographic_out_of_range_bbox_names_the_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX", "-181,0,1,1")
    monkeypatch.setenv("GEO_DECAY_BBOX_CRS", "EPSG:4326")

    with pytest.raises(ValidationError, match=r"GEO_DECAY_BBOX.*min_x"):
        _load_settings()


def test_missing_bbox_names_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX_CRS", "EPSG:25830")

    with pytest.raises(ValidationError, match="GEO_DECAY_BBOX"):
        _load_settings()


def test_missing_crs_names_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX", "10,20,30,40")

    with pytest.raises(ValidationError, match="GEO_DECAY_BBOX_CRS"):
        _load_settings()


def test_there_is_no_default_crs() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _load_settings()

    missing = {error["loc"] for error in excinfo.value.errors()}
    assert ("GEO_DECAY_BBOX_CRS",) in missing


@pytest.mark.usefixtures("valid_bbox")
@pytest.mark.parametrize("bad", ["4326", "EPSG-4326", "EPSG:"])
def test_malformed_crs_names_the_variable(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    monkeypatch.setenv("GEO_DECAY_BBOX_CRS", bad)

    with pytest.raises(ValidationError, match="GEO_DECAY_BBOX_CRS"):
        _load_settings()


@pytest.mark.usefixtures("valid_bbox")
@pytest.mark.parametrize(
    ("variable", "bad"),
    [
        ("GEO_DECAY_LOG_LEVEL", "LOUD"),
        ("GEO_DECAY_LOG_FORMAT", "xml"),
        ("GEO_DECAY_RANDOM_SEED", "not-a-number"),
    ],
)
def test_invalid_optional_setting_names_the_variable(
    monkeypatch: pytest.MonkeyPatch, variable: str, bad: str
) -> None:
    monkeypatch.setenv(variable, bad)

    with pytest.raises(ValidationError, match=variable):
        _load_settings()


def test_module_defines_no_settings_singleton() -> None:
    assert not [
        name for name, value in vars(config).items() if isinstance(value, Settings)
    ]
