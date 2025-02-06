import copy
from pathlib import Path

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language.yaml import loads

ASSET_DIR = (Path(__file__).parent / "assets" / "test_typed_configuration").resolve()


class SubConfig(Configuration):
    c: str


class Config(Configuration):
    a: int
    b: SubConfig
    config: str


def test_with_Configuration() -> None:

    config: Configuration = loads(
        """
a: 101
b:
    c: test me
config: fetchable
"""
    )
    typed = config.as_typed(Config)

    assert typed.a == 101
    assert typed.b.c == "test me"
    assert typed["a"] == 101


def test_with_LazyLoadConfiguration() -> None:
    typed = LazyLoadConfiguration(ASSET_DIR / "config.yaml").as_typed(Config)

    assert typed.a == 101
    assert typed.b.c == "test me"
    assert typed["a"] == 101
    assert typed.config == "fetchable"

    assert typed.as_dict()["config"] == "fetchable"


def test_proxy_copies_Configuration() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "config.yaml").as_typed(Config)

    assert not isinstance(config, Configuration)
    assert isinstance(copy.copy(config), Configuration)
    assert isinstance(copy.deepcopy(config), Configuration)


def test_proxy_acts_mapping() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "config.yaml").as_typed(Config)
    expected = config.as_dict()

    for key1, key2 in zip(config.keys(), expected.keys()):
        assert key1 == key2
        assert key2 in config

    assert len(config) == len(config)
