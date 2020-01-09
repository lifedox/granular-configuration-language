import importlib
import inspect
import os
import re
import sys
import typing as typ
from collections import deque
from collections.abc import MutableMapping
from functools import partial

import yaml
from yaml import MappingNode, SafeLoader, ScalarNode, SequenceNode

from granular_configuration.exceptions import ParseEnvError

consume = partial(deque, maxlen=0)

ENV_PATTERN = re.compile(r"(\{\{\s*(?P<env_name>[A-Za-z0-9-_]+)\s*(?:\:(?P<default>.*?))?\}\})")

_YNODES = typ.Union[ScalarNode, MappingNode]
_RT = typ.TypeVar("_RT")


class Placeholder:
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class LazyEval(typ.Generic[_RT]):
    def __init__(self, value: typ.Callable[[], _RT]) -> None:
        assert callable(value)
        self.value = value

    def run(self) -> _RT:
        return self.value()


def load_env(env_name: str, default: typ.Optional[str] = None) -> str:
    if default is None:
        return os.environ[env_name]
    else:
        return os.getenv(env_name, default)


def add_cwd_to_path() -> None:
    cwd = os.getcwd()
    if sys.path[0] != cwd:
        sys.path.insert(0, cwd)


def get_func(func_path: str) -> typ.Callable:
    add_cwd_to_path()
    mod_name, func = func_path.rsplit(".", 1)
    try:
        return getattr(importlib.import_module(mod_name), func)
    except (ImportError, AttributeError):
        raise ValueError("Could not load {}".format(func_path))


def handle_env(loader: SafeLoader, node: _YNODES) -> LazyEval:
    if isinstance(node, ScalarNode):
        value = loader.construct_scalar(node)
        return LazyEval(lambda: ENV_PATTERN.sub(lambda x: load_env(**x.groupdict()), value))
    else:
        raise ValueError("Only strings are supported by !Env")


def handle_placeholder(loader: SafeLoader, node: _YNODES) -> Placeholder:
    if isinstance(node, ScalarNode):
        value = loader.construct_scalar(node)
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
        value = loader.construct_scalar(node)
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


def handle_parse_env(loader: SafeLoader, node: _YNODES) -> LazyEval:
    loader_cls = loader.__class__
    if isinstance(node, ScalarNode):
        value = loader.construct_scalar(node)
        return LazyEval(lambda: parse_env(loader_cls, value))
    elif isinstance(node, SequenceNode):
        value = loader.construct_sequence(node, True)
        return LazyEval(lambda: parse_env(loader_cls, *value))
    else:
        raise ValueError("!ParseEnv only supports a string or typing.Tuple[str, typing.Any]")


def construct_mapping(cls: typ.Type[typ.Dict], loader: SafeLoader, node: _YNODES) -> typ.Dict:
    node.value = [pair for pair in node.value if pair[1].tag != "!Del"]
    loader.flatten_mapping(node)
    return cls(loader.construct_pairs(node, deep=True))


def loads(config_str: str, obj_pairs_hook: typ.Optional[typ.Type[typ.MutableMapping]] = None) -> typ.Any:
    class ExtendSafeLoader(SafeLoader):
        pass

    if obj_pairs_hook and issubclass(obj_pairs_hook, MutableMapping):
        ExtendSafeLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, partial(construct_mapping, obj_pairs_hook)
        )

    ExtendSafeLoader.add_constructor("!Env", handle_env)
    ExtendSafeLoader.add_constructor("!Func", partial(string_check, handle_func))
    ExtendSafeLoader.add_constructor("!Class", partial(string_check, handle_class))
    ExtendSafeLoader.add_constructor("!Placeholder", handle_placeholder)
    ExtendSafeLoader.add_constructor("!ParseEnv", handle_parse_env)

    return yaml.load(config_str, Loader=ExtendSafeLoader)  # nosec  # ExtendSafeLoader is a subclass of SafeLoader
