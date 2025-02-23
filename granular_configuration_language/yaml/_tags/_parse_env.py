from __future__ import annotations

import collections.abc as tabc
import os
import typing as typ
from functools import partial

from granular_configuration_language.exceptions import (
    EnvironmentVaribleNotFound,
    ParseEnvParsingError,
    ParsingTriedToCreateALoop,
)
from granular_configuration_language.yaml._parsing import (
    create_environment_variable_path,
    is_in_chain,
    make_chain_message,
)
from granular_configuration_language.yaml.classes import LazyRoot
from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    as_lazy,
    as_lazy_with_root_and_load_options,
    string_or_twople_tag,
)


def parse_env(load: tabc.Callable[[str, str], typ.Any], env_var: str, *default: typ.Any) -> typ.Any:
    env_missing = env_var not in os.environ

    if env_missing and (len(default) > 0):
        return default[0]
    elif env_missing:
        raise EnvironmentVaribleNotFound(env_var)
    else:
        try:
            return load(env_var, os.environ[env_var])
        except ParsingTriedToCreateALoop:
            raise
        except Exception as e:
            raise ParseEnvParsingError(
                f"Error while parsing Environment Variable ({env_var}): ({e.__class__.__name__}) {e}"
            ) from None


def load_advance(options: LoadOptions, root: Root, env_var: str, value: str) -> typ.Any:
    from granular_configuration_language.yaml import loads

    file_path = create_environment_variable_path(env_var)

    if is_in_chain(file_path, options):
        raise make_chain_message("!ParseEnv", env_var, options)

    lazy_root = LazyRoot.with_root(root)
    return loads(
        value,
        lazy_root=lazy_root,
        mutable=options.mutable,
        previous_options=options,
        file_path=file_path,
    )


def load_safe(env_var: str, value: str) -> typ.Any:
    from ruamel.yaml import YAML

    return YAML(typ="safe").load(value)


def parse_input(load: tabc.Callable[[str, str], typ.Any], value: string_or_twople_tag.Type) -> typ.Any:
    if isinstance(value, str):
        return parse_env(load, value)
    else:
        return parse_env(load, *value)


@string_or_twople_tag(Tag("!ParseEnv"), "Parser")
@as_lazy_with_root_and_load_options
def handler(value: string_or_twople_tag.Type, root: Root, options: LoadOptions) -> typ.Any:
    return parse_input(partial(load_advance, options, root), value)


@string_or_twople_tag(Tag("!ParseEnvSafe"), "Parser")
@as_lazy
def handler_safe(value: string_or_twople_tag.Type) -> typ.Any:
    return parse_input(load_safe, value)
