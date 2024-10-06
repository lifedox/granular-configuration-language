import os
import typing as typ
from functools import partial

from granular_configuration_language.exceptions import EnvironmentVaribleNotFound, ParseEnvParsingError
from granular_configuration_language.yaml.classes import LazyRoot
from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    as_lazy,
    as_lazy_with_root_and_load_options,
    string_or_twople_tag,
)


def parse_env(load: typ.Callable[[str], typ.Any], env_var: str, *default: typ.Any) -> typ.Any:
    env_missing = env_var not in os.environ

    if env_missing and (len(default) > 0):
        return default[0]
    elif env_missing:
        raise EnvironmentVaribleNotFound(env_var)
    else:
        try:
            return load(os.environ[env_var])
        except Exception as e:
            raise ParseEnvParsingError("Error while parsing Environment Variable ({}): {}".format(env_var, e))


def load_advance(options: LoadOptions, root: Root, value: str) -> typ.Any:
    from granular_configuration_language.yaml import loads

    lazy_root = LazyRoot.with_root(root)
    return loads(value, lazy_root=lazy_root, mutable=options.mutable)


def load_safe(value: str) -> typ.Any:
    from ruamel.yaml import YAML

    return YAML(typ="safe").load(value)


def parse_input(load: typ.Callable[[str], typ.Any], value: string_or_twople_tag.Type) -> typ.Any:
    if isinstance(value, str):
        return parse_env(load, value)
    else:
        return parse_env(load, *value)


@string_or_twople_tag(Tag("!ParseEnv"))
@as_lazy_with_root_and_load_options
def handler(value: string_or_twople_tag.Type, root: Root, options: LoadOptions) -> typ.Any:
    return parse_input(partial(load_advance, options, root), value)


@string_or_twople_tag(Tag("!ParseEnvSafe"))
@as_lazy
def handler_safe(value: string_or_twople_tag.Type) -> typ.Any:
    return parse_input(load_safe, value)
