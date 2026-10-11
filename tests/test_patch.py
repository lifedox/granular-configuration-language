from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language.exceptions import PlaceholderConfigurationError
from granular_configuration_language.mock import patch_config
from granular_configuration_language.yaml import loads

ASSET_DIR = (Path(__file__).parent / "assets" / "test_patch").resolve()


@pytest.mark.parametrize(
    "config",
    [Configuration(), Configuration(a="b"), LazyLoadConfiguration(ASSET_DIR / "simple.yaml")],
    ids=["empty", "with data", "lazy_config"],
)
def test_add_one_value(config: Configuration | LazyLoadConfiguration) -> None:
    adding = {"key": "value"}
    expected = config.as_dict()

    with patch_config(config, adding, False):
        assert config.as_dict() == {**expected, **adding}

    assert config.as_dict() == expected


@pytest.mark.parametrize(
    "config",
    [loads("key: !Placeholder sdf"), LazyLoadConfiguration(ASSET_DIR / "placeholder.yaml")],
    ids=["config", "lazy_config"],
)
def test_placeholder(config: Configuration | LazyLoadConfiguration) -> None:
    adding = {"key": "value"}

    with patch_config(config, adding, False):
        assert config.key == "value"

    with pytest.raises(PlaceholderConfigurationError):
        config.key


@pytest.mark.parametrize(
    "config",
    [loads("key: !Sub ${ENV_VAR_DOES_NOT_EXIST}"), LazyLoadConfiguration(ASSET_DIR / "sub.yaml")],
    ids=["config", "lazy_config"],
)
def test_sub(config: Configuration | LazyLoadConfiguration) -> None:
    adding = {"key": "value"}

    with patch_config(config, adding, False):
        assert config.key == "value"

    with patch.dict(os.environ, {"ENV_VAR_DOES_NOT_EXIST": "value2"}):
        assert config.key == "value2"


@pytest.mark.parametrize(
    "config",
    [Configuration(a="b", c="d"), LazyLoadConfiguration(ASSET_DIR / "simple.yaml")],
    ids=["config", "lazy_config"],
)
def test_clear(config: Configuration | LazyLoadConfiguration) -> None:
    replacement = {"key": "value"}
    expected = config.as_dict()

    with patch_config(config, replacement, True):
        assert config.as_dict() == replacement

    assert config.as_dict() == expected
