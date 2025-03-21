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
from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    as_lazy_with_load_options,
    as_lazy_with_root_and_load_options,
    string_or_twople_tag,
    with_tag,
)
from granular_configuration_language.yaml.file_loading import (
    EagerIOTextFile,
    environment_variable_as_file,
    load_safe_yaml_from_file,
    load_yaml_from_file,
)

LoadFunc = tabc.Callable[[EagerIOTextFile], typ.Any]


def parse_env(tag: Tag, options: LoadOptions, load: LoadFunc, env_var: str, *default: typ.Any) -> typ.Any:
    env_missing = env_var not in os.environ

    if env_missing and (len(default) > 0):
        return default[0]
    elif env_missing:
        raise EnvironmentVaribleNotFound(env_var)
    else:
        try:
            return load(environment_variable_as_file(tag, env_var, options))
        except ParsingTriedToCreateALoop:
            raise
        except Exception as e:
            raise ParseEnvParsingError(
                f"Error while parsing Environment Variable ({env_var}): ({e.__class__.__name__}) {e}"
            ) from None


def parse_input(tag: Tag, value: string_or_twople_tag.Type, options: LoadOptions, load: LoadFunc) -> typ.Any:
    if isinstance(value, str):
        return parse_env(tag, options, load, value)
    else:
        return parse_env(tag, options, load, *value)


@string_or_twople_tag(Tag("!ParseEnv"), "Parser")
@as_lazy_with_root_and_load_options
@with_tag
def handler(tag: Tag, value: string_or_twople_tag.Type, root: Root, options: LoadOptions) -> typ.Any:
    return parse_input(tag, value, options, partial(load_yaml_from_file, options=options, root=root))


@string_or_twople_tag(Tag("!ParseEnvSafe"), "Parser")
@as_lazy_with_load_options
@with_tag
def handler_safe(tag: Tag, value: string_or_twople_tag.Type, options: LoadOptions) -> typ.Any:
    return parse_input(tag, value, options, partial(load_safe_yaml_from_file))
