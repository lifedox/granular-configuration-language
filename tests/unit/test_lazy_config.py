import os
from functools import partial
from pathlib import Path
from unittest.mock import patch

import pytest

from granular_configuration import Configuration, ConfigurationLocations, LazyLoadConfiguration
from granular_configuration.exceptions import InvalidBasePathException

ASSET_DIR = Path(__file__).parent / "../assets/config_location_test"


class TestLaziness:

    def test_class(self) -> None:
        dir_func = partial(os.path.join, ASSET_DIR)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.yaml", "t2.yaml"]
        files = list(map(dir_func, ["g/b.yaml", "g/h.yaml"]))

        location = (
            ConfigurationLocations(files=files),
            ConfigurationLocations(filenames=filenames, directories=directories),
        )

        config_dict = Configuration({"abc": "test", "name": "me"})

        with (
            patch("granular_configuration._lazy_load.build_configuration", return_value=config_dict) as bc_mock,
            patch("granular_configuration._lazy_load.get_all_unique_locations", return_value=files) as loc_mock,
        ):
            config = LazyLoadConfiguration(*location)

            bc_mock.assert_not_called()
            loc_mock.assert_not_called()

            assert config.abc == "test"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

            assert config.name == "me"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

    def test_string_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._lazy_load.build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration(base_path="base")
            assert config._LazyLoadConfiguration__base_path == ["base"]
            bc_mock.assert_not_called()

    def test_list_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._lazy_load.build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration(base_path=["base", "path"])

            assert config._LazyLoadConfiguration__base_path == ["base", "path"]
            bc_mock.assert_not_called()

    def test_no_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._lazy_load.build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration()

            assert config._LazyLoadConfiguration__base_path == []
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
        config.load_configure()


def test_env() -> None:
    env_path = (ASSET_DIR / "test_env_config.yaml").as_posix()

    with patch("os.environ", new={"G_CONFIG_LOCATION": env_path}):
        config = LazyLoadConfiguration(
            (ASSET_DIR / "mix_config.yaml").as_posix(),
            use_env_location=True,
        )
        assert config.A.key1 == "value2"


def test_env_list() -> None:
    env_path = ",".join(((ASSET_DIR / "test_env_config.yaml").as_posix(), ((ASSET_DIR / "mix_config.yaml").as_posix())))

    with patch("os.environ", new={"G_CONFIG_LOCATION": env_path}):
        config = LazyLoadConfiguration(use_env_location=True)
        assert config.A.key1 == "value1"
        assert config.A.key2 == "MyTestValue"


def test_env_none() -> None:
    with patch("os.environ", new={}):
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
