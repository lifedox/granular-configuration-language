from __future__ import annotations

import os
import pickle
from pathlib import Path
from unittest.mock import patch

from granular_configuration_language import (
    Configuration,
    LazyLoadConfiguration,
    MutableConfiguration,
    MutableLazyLoadConfiguration,
)
from granular_configuration_language.yaml import LazyEval, loads

ASSET_DIR = (Path(__file__).parent / "assets" / "test_pickling").resolve()


def test_LazyEval_is_pickable() -> None:
    test = """\
a: !Sub ${ENV_VAR}
"""

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        a: Configuration = loads(test)
        le: LazyEval = next(a._raw_items())[1]
        serialized = pickle.dumps(le)

    with patch.dict(os.environ, values={"ENV_VAR": "test that cached_property was serialized"}):
        transformed: LazyEval = pickle.loads(serialized)
        assert transformed.result == "text"


def test_empty_Configuration_is_pickable() -> None:
    assert pickle.loads(pickle.dumps(Configuration())).as_dict() == {}


def test_Configuration_is_pickable() -> None:
    test = """\
a: !Sub ${ENV_VAR}
"""

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        serialized = pickle.dumps(loads(test))

    with patch.dict(os.environ, values={"ENV_VAR": "test that cached_property was serialized"}):
        assert pickle.loads(serialized).as_dict() == {"a": "text"}


def test_Configuration_is_pickable_with_root_lazy_eval() -> None:
    test = """\
a: !Sub ${/b}
b: text
"""

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        assert pickle.loads(pickle.dumps(loads(test))).as_dict() == {"a": "text", "b": "text"}


def test_empty_MutableConfiguration_is_pickable() -> None:
    assert pickle.loads(pickle.dumps(MutableConfiguration())).as_dict() == {}


def test_MutableConfiguration_is_pickable() -> None:
    test = """\
a: !Sub ${ENV_VAR}
"""

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        serialized = pickle.dumps(loads(test, mutable=True))

    with patch.dict(os.environ, values={"ENV_VAR": "test that cached_property was serialized"}):
        assert pickle.loads(serialized).as_dict() == {"a": "text"}


def test_LazyLoadConfiguration_is_pickable() -> None:
    llc = LazyLoadConfiguration(ASSET_DIR / "test.yaml")

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        serialized = pickle.dumps(llc)

    with patch.dict(os.environ, values={"ENV_VAR": "test that cached_property was serialized"}):
        transformed: LazyLoadConfiguration = pickle.loads(serialized)

        assert transformed.config.as_dict() == {"a": "text"}


def test_MutableLazyLoadConfiguration_is_pickable() -> None:
    llc = MutableLazyLoadConfiguration(ASSET_DIR / "test.yaml")

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        serialized = pickle.dumps(llc)

    with patch.dict(os.environ, values={"ENV_VAR": "test that cached_property was serialized"}):
        transformed: MutableLazyLoadConfiguration = pickle.loads(serialized)

        assert transformed.config.as_dict() == {"a": "text"}
