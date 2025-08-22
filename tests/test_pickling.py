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
        transformed: LazyEval = pickle.loads(pickle.dumps(le))
        assert transformed.result == "text"


def test_empty_Configuration_is_pickable() -> None:
    assert pickle.loads(pickle.dumps(Configuration())).as_dict() == {}


def test_Configuration_is_pickable() -> None:
    test = """\
a: !Sub ${ENV_VAR}
"""

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        assert pickle.loads(pickle.dumps(loads(test))).as_dict() == {"a": "text"}


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
        assert pickle.loads(pickle.dumps(loads(test, mutable=True))).as_dict() == {"a": "text"}


def test_LazyLoadConfiguration_is_pickable() -> None:
    llc = LazyLoadConfiguration(ASSET_DIR / "test.yaml")

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        transformed: LazyLoadConfiguration = pickle.loads(pickle.dumps(llc))

        assert transformed.config.as_dict() == {"a": "text"}


def test_MutableLazyLoadConfiguration_is_pickable() -> None:
    llc = MutableLazyLoadConfiguration(ASSET_DIR / "test.yaml")

    with patch.dict(os.environ, values={"ENV_VAR": "text"}):
        transformed: MutableLazyLoadConfiguration = pickle.loads(pickle.dumps(llc))

        assert transformed.config.as_dict() == {"a": "text"}
