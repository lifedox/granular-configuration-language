from functools import reduce

import pytest

from granular_configuration import Masked
from granular_configuration._json import dumps
from granular_configuration.exceptions import DoesNotExist, IsNotAClass, IsNotCallable
from granular_configuration.yaml import loads


def test_func_loads_function() -> None:
    assert loads("!Func functools.reduce") is reduce
    assert loads("!Func granular_configuration.Masked") is Masked
    assert (
        dumps(loads("!Func granular_configuration.yaml.loads"))
        == '''"<granular_configuration.yaml.load._external.external>"'''
    )
    assert (
        dumps(loads("!Func granular_configuration._utils.consume"))
        == '''"<functools.partial(<class 'collections.deque'>, maxlen=0)>"'''
    )


def test_class_loads_class() -> None:
    assert loads("!Class granular_configuration.Masked") is Masked
    assert dumps(loads("!Class granular_configuration.Masked")) == '"<granular_configuration.yaml.classes.Masked>"'


def test_loading_something_that_does_not_throw_exception() -> None:
    with pytest.raises(DoesNotExist):
        loads("!Func unreal.garbage.func")
    with pytest.raises(DoesNotExist):
        loads("!Class unreal.garbage.func")


def test_func_not_callable_throws_exception() -> None:
    with pytest.raises(IsNotCallable):
        loads("!Func sys.stdout")


def test_class_not_a_class_throws_exception() -> None:
    with pytest.raises(IsNotAClass):
        loads("!Class functools.reduce")
