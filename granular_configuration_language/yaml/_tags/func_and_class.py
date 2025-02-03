import collections.abc as tabc
import importlib
import inspect
import os
import sys

from granular_configuration_language.exceptions import DoesNotExist, IsNotAClass, IsNotCallable
from granular_configuration_language.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag


def add_cwd_to_path() -> None:
    cwd = os.getcwd()
    if sys.path[0] != cwd:  # pragma: no cover
        sys.path.insert(0, cwd)


def get_func(func_path: str) -> tabc.Callable:
    add_cwd_to_path()
    mod_name, func_name = func_path.rsplit(".", 1)
    try:
        func: tabc.Callable = getattr(importlib.import_module(mod_name), func_name)
        return func
    except (ImportError, AttributeError):
        raise DoesNotExist(f"Could not load {func_path}")


@string_tag(Tag("!Class"))
@as_lazy
@interpolate_value_without_ref
def class_handler(value: str) -> tabc.Callable:
    class_type = get_func(value)
    if inspect.isclass(class_type):
        return class_type
    else:
        raise IsNotAClass(f"Classes loaded by !Class must pass `inspect.isclass`: `{value}` is not a class")


@string_tag(Tag("!Func"))
@as_lazy
@interpolate_value_without_ref
def func_handler(value: str) -> tabc.Callable:
    func = get_func(value)
    if callable(func):
        return func
    else:
        raise IsNotCallable(f"Functions loaded by !Func must be callable: `{value}` is not callble")
