from __future__ import annotations

import importlib
import inspect
import operator as op
import os
import re
import sys
import typing as typ
from collections.abc import MutableMapping
from functools import partial
from pathlib import Path

from ruamel.yaml import YAML

import jsonpath_rw
import yaml
from yaml import MappingNode, SafeLoader, ScalarNode, SequenceNode

from granular_configuration.exceptions import ParseEnvError
from granular_configuration.yaml_handler.classes import LazyEval, LazyEvalRootStateStr, LazyRoot, Placeholder, LazyEvalStr

_OPH = typ.Optional[typ.Type[typ.MutableMapping]]

ENV_PATTERN: typ.Pattern[str] = re.compile(r"(\{\{\s*(?P<env_name>[A-Za-z0-9-_]+)\s*(?:\:(?P<default>.*?))?\}\})")
SUB_PATTERN: typ.Pattern[str] = re.compile(r"(\$\{(?P<contents>.*?)\})")

_YNODES = typ.Union[ScalarNode, MappingNode]



if typ.TYPE_CHECKING:  # pragma: no cover

    class ExtendSafeLoader(SafeLoader):
        lazy_root_obj: LazyRoot
        obj_pairs_func: _OPH
        file_relative_path: Path


def load_env(env_name: str, default: typ.Optional[str] = None) -> str:
    if default is None:
        return os.environ[env_name]
    else:
        return os.getenv(env_name, default)


def load_sub(root: typ.Mapping, *, contents: str) -> str:
    if contents.startswith("$"):
        result = list(map(op.attrgetter("value"), jsonpath_rw.parse(contents).find(root)))
        if len(result) == 1:
            return str(result[0])
        elif len(result) == 0:
            raise KeyError(contents)
        else:
            return repr(result)
    else:
        env_params = contents.split(":-", maxsplit=1)
        if len(env_params) > 1:
            return os.getenv(env_params[0], env_params[1])
        else:
            return os.environ[env_params[0]]


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


def handle_env(loader: SafeLoader, node: _YNODES) -> LazyEvalStr:
    if isinstance(node, ScalarNode):
        value: str = loader.construct_scalar(node)
        return LazyEvalStr(lambda: ENV_PATTERN.sub(lambda x: load_env(**x.groupdict()), value))
    else:
        raise ValueError("Only strings are supported by !Env")


def handle_sub(loader: "ExtendSafeLoader", node: _YNODES) -> LazyEvalRootStateStr:
    if isinstance(node, ScalarNode):
        value: str = loader.construct_scalar(node)
        return LazyEvalRootStateStr(
            loader.lazy_root_obj, lambda root: SUB_PATTERN.sub(lambda x: load_sub(root, **x.groupdict()), value)
        )
    else:
        raise ValueError("Only strings are supported by !Sub")


def handle_placeholder(loader: SafeLoader, node: _YNODES) -> Placeholder:
    if isinstance(node, ScalarNode):
        value: str = loader.construct_scalar(node)
        return Placeholder(value)
    else:
        raise ValueError("Only strings are supported by !Placeholder")


def handle_class(value: str) -> typ.Callable:
    class_type = get_func(value)
    if inspect.isclass(class_type):
        return class_type
    else:
        raise ValueError("Classes loaded by !Class must subclass object")


def handle_func(value: str) -> typ.Callable:
    func = get_func(value)
    if not callable(func):
        raise ValueError("Functions loaded by !Func must be callable")
    else:
        return func


def string_check(func: typ.Callable[[str], _RT], loader: SafeLoader, node: _YNODES) -> LazyEval[_RT]:
    if isinstance(node, ScalarNode):
        value: str = loader.construct_scalar(node)
        return LazyEval(lambda: func(value))
    else:
        raise ValueError("Only strings are supported by !{}".format(node.tag))


def parse_env(loader_cls: typ.Type[SafeLoader], env_var: str, *default: typ.Any) -> typ.Any:
    env_var = str(env_var)
    env_missing = env_var not in os.environ

    if env_missing and (len(default) > 0):
        return default[0]
    elif env_missing:
        raise KeyError(env_var)
    else:
        try:
            value = yaml.load(  # nosec
                os.environ[env_var], Loader=loader_cls
            )  # ExtendSafeLoader is a subclass of SafeLoader
        except Exception as e:
            raise ParseEnvError("Error while parsing Environment Variable ({}): {}".format(env_var, e))
        if isinstance(value, LazyEval):
            return value.run()
        else:
            return value


def handle_parse_env(loader: SafeLoader, node: _YNODES) -> LazyEval[typ.Any]:
    loader_cls = loader.__class__
    if isinstance(node, ScalarNode):
        value = loader.construct_scalar(node)
        return LazyEval(lambda: parse_env(loader_cls, value))
    elif isinstance(node, SequenceNode):
        value = loader.construct_sequence(node, True)
        return LazyEval(lambda: parse_env(loader_cls, *value))
    else:
        raise ValueError("!ParseEnv only supports a string or typing.Tuple[str, typing.Any]")


def handle_parse_file(loader: ExtendSafeLoader, node: _YNODES) -> typ.Any:
    # This is a cyclical dependency
    from granular_configuration._load import load_file

    if isinstance(node, ScalarNode):
        value: str = loader.construct_scalar(node)
        return load_file(
            loader.file_relative_path / value, obj_pairs_hook=loader.obj_pairs_func, lazy_root=loader.lazy_root_obj
        )
    elif isinstance(node, SequenceNode):
        raise ValueError("!ParseFile only supports a string")
    else:
        raise ValueError("!ParseFile only supports a string or typing.Tuple[str, typing.Any]")


def construct_mapping(cls: typ.Type[typ.Dict], loader: SafeLoader, node: _YNODES) -> typ.Dict:
    node.value = [pair for pair in node.value if pair[1].tag != "!Del"]
    loader.flatten_mapping(node)
    return cls(loader.construct_pairs(node, deep=True))


def loads_v1(
    config_str: str,
    obj_pairs_hook: _OPH = None,
    *,
    lazy_root: typ.Optional[LazyRoot] = None,
    file_path: typ.Optional[Path] = None,
) -> typ.Any:
    class ExtendSafeLoader(SafeLoader):
        lazy_root_obj = lazy_root or LazyRoot()
        obj_pairs_func = obj_pairs_hook
        file_relative_path = file_path.parent if file_path is not None else Path(".")
        pass

    if obj_pairs_hook and issubclass(obj_pairs_hook, MutableMapping):
        ExtendSafeLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, partial(construct_mapping, obj_pairs_hook)
        )

    ExtendSafeLoader.add_constructor("!Env", handle_env)
    ExtendSafeLoader.add_constructor("!Sub", handle_sub)
    ExtendSafeLoader.add_constructor("!Func", partial(string_check, handle_func))
    ExtendSafeLoader.add_constructor("!Class", partial(string_check, handle_class))
    ExtendSafeLoader.add_constructor("!Placeholder", handle_placeholder)
    ExtendSafeLoader.add_constructor("!ParseEnv", handle_parse_env)
    ExtendSafeLoader.add_constructor("!ParseFile", handle_parse_file)

    result = yaml.load(config_str, Loader=ExtendSafeLoader)  # nosec  # ExtendSafeLoader is a subclass of SafeLoader
    ExtendSafeLoader.lazy_root_obj.root = result
    return result

def loads_v2(
    config_str: str,
    obj_pairs_hook: _OPH = None,
    *,
    lazy_root: typ.Optional[LazyRoot] = None,
    file_path: typ.Optional[Path] = None,
) -> typ.Any:

    yaml = YAML(typ="safe")

    yaml.constructor

    



loads = loads_v1