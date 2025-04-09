from __future__ import annotations

import copy
import gc
import threading
import weakref
from pathlib import Path

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language.proxy import EagerIOConfigurationProxy

ASSET_DIR = (Path(__file__).parent / "assets" / "test_typed_configuration").resolve()
EAGER_DIR = (Path(__file__).parent / "assets" / "test_eager_parse_file").resolve()


class SubConfig(Configuration):
    c: str


class Config(Configuration):
    a: int
    b: SubConfig
    config: str


def test_with_LazyLoadConfiguration() -> None:
    typed = LazyLoadConfiguration(ASSET_DIR / "config.yaml").eager_load(Config)

    assert typed.a == 101
    assert typed.b.c == "test me"
    assert typed["a"] == 101
    assert typed.config == "fetchable"

    assert typed.as_dict()["config"] == "fetchable"


def test_proxy_copies_Configuration() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "config.yaml").eager_load(Config)

    assert isinstance(copy.copy(config), Configuration)
    assert isinstance(copy.deepcopy(config), Configuration)
    assert isinstance(config, Configuration)
    assert isinstance(config, EagerIOConfigurationProxy)


def test_proxy_acts_mapping() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "config.yaml").eager_load(Config)
    expected = config.as_dict()

    for key1, key2 in zip(config.keys(), expected.keys()):
        assert key1 == key2
        assert key2 in config

    assert len(config) == len(config)


def test_construction() -> None:
    typed = Config(a=101, b=SubConfig(c="test me"), config="test me")

    assert typed.a == 101
    assert typed.b.c == "test me"
    assert typed["a"] == 101


def test_SimpleFuture_deconstructs_when_result_is_not_used() -> None:
    config = LazyLoadConfiguration(EAGER_DIR / "parsefile1.yaml").eager_load(Config)

    assert threading.active_count() > 1

    config_wref = weakref.ref(config)
    future_wref = weakref.ref(config._EagerIOConfigurationProxy__future)

    del config

    gc.collect()

    assert config_wref() is None
    assert future_wref() is None

    assert threading.active_count() == 1
