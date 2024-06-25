import os
import typing as typ
from functools import partial

from granular_configuration.exceptions import ParseEnvEnvironmentVaribleNotFound, ParseEnvError
from granular_configuration.yaml.classes import _OPH, LazyEval, LazyRoot, Root, StateOptions
from granular_configuration.yaml.decorators import (
    StringOrTwopleTagType,
    Tag,
    make_lazy,
    make_lazy_root_with_state,
    string_or_twople_tag,
)


def parse_env(load: typ.Callable[[str], typ.Any], env_var: str, *default: typ.Any) -> typ.Any:
    env_var = str(env_var)
    env_missing = env_var not in os.environ

    if env_missing and (len(default) > 0):
        return default[0]
    elif env_missing:
        raise ParseEnvEnvironmentVaribleNotFound(env_var)
    else:
        try:
            return load(os.environ[env_var])
        except Exception as e:
            raise ParseEnvError("Error while parsing Environment Variable ({}): {}".format(env_var, e))


def load_advance(obj_pair_hook: _OPH, root: Root, value: str) -> typ.Any:
    from granular_configuration.yaml import loads

    lazy_root = LazyRoot()
    lazy_root._set_root(root)
    value = loads(value, obj_pairs_hook=obj_pair_hook, lazy_root=lazy_root)
    while isinstance(value, LazyEval):
        return value.run()
    return value


def load_safe(value: str) -> typ.Any:
    from ruamel.yaml import YAML

    return YAML(typ="safe").load(value)


def parse_input(load: typ.Callable[[str], typ.Any], value: StringOrTwopleTagType) -> typ.Any:
    if isinstance(value, str):
        return parse_env(load, value)
    else:
        return parse_env(load, *value)


@string_or_twople_tag(Tag("!ParseEnv"))
@make_lazy_root_with_state
def handler(value: StringOrTwopleTagType, options: StateOptions, root: Root) -> typ.Any:
    return parse_input(partial(load_advance, options.obj_pairs_func, root), value)


@string_or_twople_tag(Tag("!ParseEnvSafe"))
@make_lazy
def handler_safe(value: StringOrTwopleTagType) -> typ.Any:
    return parse_input(load_safe, value)
