from __future__ import annotations

import collections.abc as tabc
import operator as op
import os
from contextlib import AbstractContextManager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from granular_configuration_language import Configuration, LazyLoadConfiguration, MutableLazyLoadConfiguration
from granular_configuration_language._lazy_load_configuration import Locations
from granular_configuration_language.exceptions import (
    EnvironmentVaribleNotFound,
    ErrorWhileLoadingFileOccurred,
    IniUnsupportedError,
    InvalidBasePathException,
    ReservedFileExtension,
)
from granular_configuration_language.yaml.file_ops.environment_variable import ENV_VAR_FILE_EXTENSION

ASSET_DIR = (Path(__file__).parent / "assets" / "test_lazy_config").resolve()


def as_env_var_list(*file_names: str) -> str:
    return ",".join(map(op.methodcaller("as_posix"), map(ASSET_DIR.__truediv__, file_names)))


def build_configuration_pach() -> AbstractContextManager[AsyncMock | MagicMock]:
    from granular_configuration_language._cache import build_configuration

    return patch("granular_configuration_language._cache.build_configuration", side_effect=build_configuration)


@pytest.mark.parametrize(
    "creator,mutable",
    (
        (lambda files: LazyLoadConfiguration(*files), False),
        (lambda files: LazyLoadConfiguration(*files).as_typed(Configuration), False),
        (lambda files: MutableLazyLoadConfiguration(*files), True),
    ),
    ids=("class", "proxy", "mutable_class"),
)
def test_laziness(
    creator: tabc.Callable[[tabc.Iterable[Path]], LazyLoadConfiguration | Configuration],
    mutable: bool,
) -> None:
    with build_configuration_pach() as bc_mock:
        files = [ASSET_DIR / "test_env_config.yaml"]

        config = creator(files)

        bc_mock.assert_not_called()

        assert config.A.key1 == "value2"
        assert config.A.key2 == "MyTestValue"

        bc_mock.assert_called_once_with(Locations(files), mutable, inject_before=None, inject_after=None)


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
    env_path = as_env_var_list("test_env_config.yaml")

    with patch.dict(os.environ, values={"G_CONFIG_LOCATION": env_path}):
        config = LazyLoadConfiguration(
            (ASSET_DIR / "mix_config.yaml").as_posix(),
            use_env_location=True,
        )
        assert config.A.key1 == "value2"


def test_env_list() -> None:
    env_path = as_env_var_list("test_env_config.yaml", "mix_config.yaml")

    with patch.dict(os.environ, values={"G_CONFIG_LOCATION": env_path}):
        config = LazyLoadConfiguration(use_env_location=True)
        assert config.A.key1 == "value1"
        assert config.A.key2 == "MyTestValue"


def test_changing_env_var_name_enables_env() -> None:
    env_path = as_env_var_list("test_env_config.yaml", "mix_config.yaml")

    with patch.dict(os.environ, values={"TEST_G_CONFIG_LOCATION": env_path}):
        config = LazyLoadConfiguration(env_location_var_name="TEST_G_CONFIG_LOCATION")
        assert config.A.key1 == "value1"
        assert config.A.key2 == "MyTestValue"


def test_env_none() -> None:
    with patch.dict(os.environ, values={}):
        config = LazyLoadConfiguration(use_env_location=True)
        assert config.as_dict() == {}


def test_like_a_mapping() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "test_env_config.yaml")

    assert config["A"]["key1"] == "value2"
    assert len(config) == 1
    assert list(config) == ["A"]
    assert "A" in config


def test_MutableLazyLoadConfiguration_is_like_a_mutablemapping() -> None:
    config = MutableLazyLoadConfiguration(ASSET_DIR / "test_env_config.yaml")

    assert config["A"]["key1"] == "value2"
    config["B"] = 1
    assert config["B"] == 1
    assert len(config) == 2
    del config["B"]
    assert list(config) == ["A"]


def test_loading_empty_is_an_empty_dict() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "empty.yaml").config.as_dict() == {}


def test_loading_bad_yaml_causes_error() -> None:
    with pytest.raises(ErrorWhileLoadingFileOccurred):
        LazyLoadConfiguration(ASSET_DIR / "bad.txt").config


def test_loading_ini_causes_error() -> None:
    with pytest.raises(IniUnsupportedError):
        LazyLoadConfiguration(ASSET_DIR / "dummy.ini").config


def test_missing_environment_variable_in_base_path() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(EnvironmentVaribleNotFound):
            LazyLoadConfiguration(ASSET_DIR / "bad_env_var_base_path.yaml", base_path=tuple("ab")).config


def test_loading_environment_variable_file_extension_fails() -> None:
    with pytest.raises(ReservedFileExtension):
        LazyLoadConfiguration(ASSET_DIR / ("bad" + ENV_VAR_FILE_EXTENSION)).config
