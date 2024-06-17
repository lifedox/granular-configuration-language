import importlib
import inspect
import os
import sys
import typing as typ

from granular_configuration.yaml_handler.decorators import make_lazy, string_only_tag


def add_cwd_to_path() -> None:
    cwd = os.getcwd()
    if sys.path[0] != cwd:
        sys.path.insert(0, cwd)


def get_func(func_path: str) -> typ.Callable:
    add_cwd_to_path()
    mod_name, func_name = func_path.rsplit(".", 1)
    try:
        func: typ.Callable = getattr(importlib.import_module(mod_name), func_name)
        return func
    except (ImportError, AttributeError):
        raise ValueError(f"Could not load {func_path}")


@string_only_tag("!Class")
@make_lazy
def class_handler(value: str) -> typ.Callable:
    class_type = get_func(value)
    if inspect.isclass(class_type):
        return class_type
    else:
        raise ValueError("Classes loaded by !Class must subclass object")


@string_only_tag("!Func")
@make_lazy
def func_handler(value: str) -> typ.Callable:
    func = get_func(value)
    if not callable(func):
        raise ValueError("Functions loaded by !Func must be callable")
    else:
        return func
