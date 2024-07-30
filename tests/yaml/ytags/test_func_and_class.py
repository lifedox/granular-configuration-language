from functools import reduce

from granular_configuration import Masked
from granular_configuration.yaml import loads


def test_func() -> None:
    assert loads("!Func functools.reduce") is reduce
    assert loads("!Func granular_configuration.Masked") is Masked


def test_class() -> None:
    assert loads("!Class granular_configuration.Masked") is Masked
