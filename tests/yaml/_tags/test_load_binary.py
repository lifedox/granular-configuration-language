from __future__ import annotations

from pathlib import Path

import pytest

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language.yaml import loads

ASSET_DIR = (Path(__file__).parent / "../../assets/" / "test_load_bindary").resolve()


class Config(Configuration):
    data: bytes


def test_loads_bytes_from_file() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "binary.yaml").as_typed(Config).data == b"hello"


def test_eager_loads_bytes_from_file() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "eager.yaml").as_typed(Config).data == b"hello"


def test_eager_loading_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        loads("!EagerLoadBinary does_not_exist.bin", file_path=ASSET_DIR / "dummy.yaml")


def test_loading_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        loads("!LoadBinary does_not_exist.bin", file_path=ASSET_DIR / "dummy.yaml")
