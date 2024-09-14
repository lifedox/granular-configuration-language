from __future__ import annotations

import re
import typing as typ
import warnings
from functools import wraps
from html import unescape

from granular_configuration._utils import get_environment_variable
from granular_configuration.exceptions import InterpolationSyntaxError, InterpolationWarning
from granular_configuration.yaml.classes import Root
from granular_configuration.yaml.decorators._interpolate._env_var_parser import parse_environment_variable_syntax
from granular_configuration.yaml.decorators._tag_tracker import track_as_with_ref, track_as_without_ref
from granular_configuration.yaml.decorators.ref import resolve_json_ref

_P = typ.ParamSpec("_P")
_RT = typ.TypeVar("_RT")


def _get_ref_string(root: Root, contents: str) -> str:
    value = resolve_json_ref(contents, root)
    if isinstance(value, str):
        return value
    elif isinstance(value, (typ.Mapping, typ.Sequence)):
        return repr(value)
    else:
        return str(value)


def _get_env_var_string(root: Root, contents: str) -> str:
    parser = parse_environment_variable_syntax(contents)
    match parser.mode:
        case "":
            return get_environment_variable(contents[parser.name])
        case "-":
            return get_environment_variable(contents[parser.name], contents[parser.value])
        case "+":
            return get_environment_variable(
                contents[parser.name], lambda: curly_sub(root, contents=contents[parser.value])
            )
        case _:
            raise InterpolationSyntaxError(
                f'":{parser.mode}" is not a supported environment variable interpolation mode.'
            )


def curly_sub(root: Root, *, contents: str) -> str:
    if contents == "":
        raise InterpolationSyntaxError('"${}"" is not a supported environment variable interpolation syntax.')
    elif contents == "$":
        return "$"
    elif root and contents.startswith("$") or contents.startswith("/"):
        return _get_ref_string(root, contents)
    elif contents.startswith("&") and contents.endswith(";"):
        return unescape(contents)
    else:
        return _get_env_var_string(root, contents)


def round_sub(root: Root, *, contents: str) -> str:
    warnings.warn("`!Sub $()` is reserved", InterpolationWarning)
    return "$(" + contents + ")"


def square_sub(root: Root, *, contents: str) -> str:
    warnings.warn("`!Sub $[]` is reserved", InterpolationWarning)
    return "$[" + contents + "]"


SUB_PATTERNS: typ.Final[typ.Sequence[tuple[typ.Callable, typ.Pattern[str]]]] = (
    (round_sub, re.compile(r"(\$\((?P<contents>.*?)\))")),
    (square_sub, re.compile(r"(\$\[(?P<contents>.*?)\])")),
    (curly_sub, re.compile(r"(\$\{(?P<contents>.*?)\})")),
)


def interpolate(value: str, root: Root) -> str:
    for sub, pat in SUB_PATTERNS:
        value = pat.sub(lambda x: sub(root, **x.groupdict()), value)
    return value


def interpolate_value_with_ref(
    func: typ.Callable[typ.Concatenate[str, Root, _P], _RT]
) -> typ.Callable[typ.Concatenate[str, Root, _P], _RT]:
    @wraps(func)
    def lazy_wrapper(value: str, root: Root, *args: _P.args, **kwargs: _P.kwargs) -> _RT:
        return func(interpolate(value, root), root, *args, **kwargs)

    track_as_with_ref(func)
    return lazy_wrapper


def interpolate_value_without_ref(
    func: typ.Callable[typ.Concatenate[str, _P], _RT]
) -> typ.Callable[typ.Concatenate[str, _P], _RT]:
    @wraps(func)
    def lazy_wrapper(value: str, *args: _P.args, **kwargs: _P.kwargs) -> _RT:
        return func(interpolate(value, None), *args, **kwargs)

    track_as_without_ref(func)
    return lazy_wrapper