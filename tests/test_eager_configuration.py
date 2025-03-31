from __future__ import annotations

import copy
from pathlib import Path

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language.proxy import EagerIOConfigurationProxy

ASSET_DIR = (Path(__file__).parent / "assets" / "test_typed_configuration").resolve()


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
