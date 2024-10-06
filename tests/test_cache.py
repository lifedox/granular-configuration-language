import os
from pathlib import Path
from unittest.mock import patch
from weakref import WeakValueDictionary

import pytest

from granular_configuration_language import LazyLoadConfiguration
from granular_configuration_language.exceptions import EnvironmentVaribleNotFound, InvalidBasePathException

ASSET_DIR = (Path(__file__).parent / "assets" / "test_cache").resolve()


@patch("granular_configuration_language._cache.store", new_callable=WeakValueDictionary)
def test_shared_config(store: WeakValueDictionary) -> None:
    c1 = LazyLoadConfiguration(ASSET_DIR / "simple.yaml")
    c2 = LazyLoadConfiguration(ASSET_DIR / "simple.yaml")

    assert len(store) == 1, repr(dict(store))

    config1 = c1.config

    assert len(store) == 0, repr(dict(store))

    assert config1 is c2.config

    assert len(store) == 0, repr(dict(store))

    assert c2.config == {"a": 1}


@patch("granular_configuration_language._cache.store", new_callable=WeakValueDictionary)
def test_shared_config_with_good_base_paths(store: WeakValueDictionary) -> None:
    c1 = LazyLoadConfiguration(ASSET_DIR / "1_level.yaml", base_path="a")
    c2 = LazyLoadConfiguration(ASSET_DIR / "1_level.yaml", base_path="c")

    assert len(store) == 1, repr(dict(store))

    c1.config

    assert len(store) == 0, repr(dict(store))

    c2.config

    assert len(store) == 0, repr(dict(store))

    assert c1.config == {"b": 1}
    assert c2.config == {"d": 2}


@patch("granular_configuration_language._cache.store", new_callable=WeakValueDictionary)
def test_shared_config_with_a_good_and_a_bad_base_path(store: WeakValueDictionary) -> None:
    c1 = LazyLoadConfiguration(ASSET_DIR / "1_level.yaml", base_path="a")
    c2 = LazyLoadConfiguration(ASSET_DIR / "1_level.yaml", base_path="does_not_exist_path")

    assert len(store) == 1, repr(dict(store))

    c1.config

    assert len(store) == 1, repr(dict(store))

    with pytest.raises(InvalidBasePathException, match="does_not_exist_path"):
        c2.config

    assert len(store) == 1, repr(dict(store))

    assert c1.config == {"b": 1}


@patch("granular_configuration_language._cache.store", new_callable=WeakValueDictionary)
def test_shared_config_with_base_base_paths(store: WeakValueDictionary) -> None:
    c1 = LazyLoadConfiguration(ASSET_DIR / "1_level.yaml", base_path="does_not_exist_path1")
    c2 = LazyLoadConfiguration(ASSET_DIR / "1_level.yaml", base_path="does_not_exist_path2")

    assert len(store) == 1, repr(dict(store))

    with pytest.raises(InvalidBasePathException, match="does_not_exist_path1"):
        c1.config

    assert len(store) == 1, repr(dict(store))

    with pytest.raises(InvalidBasePathException, match="does_not_exist_path2"):
        c2.config

    assert len(store) == 1, repr(dict(store))


@patch("granular_configuration_language._cache.store", new_callable=WeakValueDictionary)
def test_shared_config_when_disable_caching(store: WeakValueDictionary) -> None:
    c1 = LazyLoadConfiguration(ASSET_DIR / "simple.yaml", disable_caching=True)
    c2 = LazyLoadConfiguration(ASSET_DIR / "simple.yaml", disable_caching=True)

    assert len(store) == 0, repr(dict(store))

    config1 = c1.config

    assert len(store) == 0, repr(dict(store))

    assert config1 == c2.config
    assert config1 is not c2.config

    assert len(store) == 0, repr(dict(store))

    assert c2.config == {"a": 1}


@patch("granular_configuration_language._cache.store", new_callable=WeakValueDictionary)
def test_shared_config_EnvironmentVaribleNotFound_error(store: WeakValueDictionary) -> None:
    with patch.dict(os.environ, values={}):
        c1 = LazyLoadConfiguration(ASSET_DIR / "env.yaml", base_path="good")
        c2 = LazyLoadConfiguration(ASSET_DIR / "env.yaml", base_path=["bad"])

        assert len(store) == 1, repr(dict(store))

        assert c1._LazyLoadConfiguration__receipt is not None
        assert c2._LazyLoadConfiguration__receipt is not None
        assert hasattr(c1._LazyLoadConfiguration__receipt, "_config_ref")
        assert hasattr(c2._LazyLoadConfiguration__receipt, "_config_ref")

        c1.config

        assert len(store) == 1, repr(dict(store))

        assert c1._LazyLoadConfiguration__receipt is None
        assert c2._LazyLoadConfiguration__receipt is not None
        assert not hasattr(c2._LazyLoadConfiguration__receipt, "_config_ref")

        with pytest.raises(EnvironmentVaribleNotFound):
            c2.config

        assert len(store) == 1, repr(dict(store))

        assert c1.config == {"a": 1}
