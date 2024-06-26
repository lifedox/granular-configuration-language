import importlib
import inspect
import os
import sys
import typing as typ

from granular_configuration.yaml.decorators import Tag, as_lazy, string_tag


def add_cwd_to_path() -> None:
    cwd = os.getcwd()
    if sys.path[0] != cwd:  # pragma: no cover
        sys.path.insert(0, cwd)


def get_func(func_path: str) -> typ.Callable:
    add_cwd_to_path()
    mod_name, func_name = func_path.rsplit(".", 1)
    try:
        func: typ.Callable = getattr(importlib.import_module(mod_name), func_name)
        return func
    except (ImportError, AttributeError):
        raise ValueError(f"Could not load {func_path}")


@string_tag(Tag("!Class"))
@as_lazy
def class_handler(value: str) -> typ.Callable:
    class_type = get_func(value)
    if inspect.isclass(class_type):
        return class_type
    else:
        raise ValueError("Classes loaded by !Class must pass `inspect.isclass`")


@string_tag(Tag("!Func"))
@as_lazy
def func_handler(value: str) -> typ.Callable:
    func = get_func(value)
    if not callable(func):
        raise ValueError("Functions loaded by !Func must be callable")
    else:
        return func
