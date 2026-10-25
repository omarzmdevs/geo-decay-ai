"""Smoke test: the four layer packages of the skeleton are importable."""

import importlib

import pytest

PACKAGES = [
    "geo_decay_domain",
    "geo_decay_data",
    "geo_decay_application",
    "geo_decay_delivery",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_package_is_importable(name: str) -> None:
    assert importlib.import_module(name).__name__ == name
