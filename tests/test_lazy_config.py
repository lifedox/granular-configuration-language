import os
from pathlib import Path
from unittest.mock import patch

import pytest

from granular_configuration import Configuration, LazyLoadConfiguration
from granular_configuration._lazy_load import Locations, build_configuration
from granular_configuration.exceptions import IniUnsupportedError, InvalidBasePathException

ASSET_DIR = (Path(__file__).parent / "assets").resolve()


class TestLaziness:

    def test_class(self) -> None:
        with (
            patch("granular_configuration._lazy_load.build_configuration", side_effect=build_configuration) as bc_mock,
        ):
            files = [ASSET_DIR / "test_env_config.yaml"]

            config = LazyLoadConfiguration(*files)

            bc_mock.assert_not_called()
            assert list(config._LazyLoadConfiguration__locations) == files

            assert config.A.key1 == "value2"
            assert config.A.key2 == "MyTestValue"

            bc_mock.assert_called_once_with(Locations(files))

    def test_string_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._lazy_load.build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration(base_path="base")
            assert list(config._LazyLoadConfiguration__base_path) == ["base"]
            bc_mock.assert_not_called()

    def test_list_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._lazy_load.build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration(base_path=["base", "path"])

            assert list(config._LazyLoadConfiguration__base_path) == ["base", "path"]
            bc_mock.assert_not_called()

    def test_no_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._lazy_load.build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration()

            assert list(config._LazyLoadConfiguration__base_path) == []
            bc_mock.assert_not_called()


def test_with_base_path() -> None:
    location = (
        ASSET_DIR / "base_path1.yaml",
        ASSET_DIR / "base_path2.yaml",
    )
    config = LazyLoadConfiguration(*location, base_path=["start", "id"])

    assert config.abc == "test"
    assert config.name == "me"


def test_get() -> None:
    location = (
        ASSET_DIR / "base_path1.yaml",
        ASSET_DIR / "base_path2.yaml",
    )
    config = LazyLoadConfiguration(*location, base_path=["start", "id"])

    assert config.get("abc") == "test"
    assert config.get("name") == "me"


def test_bad_base_path() -> None:
    config = LazyLoadConfiguration(base_path="base")

    with pytest.raises(InvalidBasePathException):
        config.load_configuration()


def test_env() -> None:
    env_path = (ASSET_DIR / "test_env_config.yaml").as_posix()

    with patch.dict(os.environ, values={"G_CONFIG_LOCATION": env_path}):
        config = LazyLoadConfiguration(
            (ASSET_DIR / "mix_config.yaml").as_posix(),
            use_env_location=True,
        )
        assert config.A.key1 == "value2"


def test_env_list() -> None:
    env_path = ",".join(((ASSET_DIR / "test_env_config.yaml").as_posix(), ((ASSET_DIR / "mix_config.yaml").as_posix())))

    with patch.dict(os.environ, values={"G_CONFIG_LOCATION": env_path}):
        config = LazyLoadConfiguration(use_env_location=True)
        assert config.A.key1 == "value1"
        assert config.A.key2 == "MyTestValue"


def test_env_none() -> None:
    with patch.dict(os.environ, values={}):
        config = LazyLoadConfiguration(use_env_location=True)
        assert config.as_dict() == {}


def test_like_a_mutablemapping() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "test_env_config.yaml")

    assert config["A"]["key1"] == "value2"
    config["B"] = 1
    assert config["B"] == 1
    assert len(config) == 2
    del config["B"]
    assert list(config) == ["A"]


def test_loading_empty_is_an_empty_dict() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "empty.yaml").config.as_dict() == {}


def test_loading_bad_yaml_causes_error() -> None:
    with pytest.raises(ValueError):
        LazyLoadConfiguration(ASSET_DIR / "bad.txt").config


def test_loading_ini_causes_error() -> None:
    with pytest.raises(IniUnsupportedError):
        LazyLoadConfiguration(ASSET_DIR / "dummy.ini").config
