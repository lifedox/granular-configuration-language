from __future__ import annotations

import collections.abc as tabc
import re
import typing as typ
import warnings
from functools import partial
from html import unescape

from granular_configuration_language._utils import get_environment_variable
from granular_configuration_language.exceptions import InterpolationSyntaxError, InterpolationWarning
from granular_configuration_language.yaml.classes import RT, P, Root
from granular_configuration_language.yaml.decorators._tag_tracker import tracker
from granular_configuration_language.yaml.decorators.interpolate._env_var_parser import (
    parse_environment_variable_syntax,
)
from granular_configuration_language.yaml.decorators.ref import resolve_json_ref


def _get_ref_string(root: Root, contents: str) -> str:
    value = resolve_json_ref(contents, root)
    if isinstance(value, str):
        return value
    elif isinstance(value, tabc.Mapping | tabc.Sequence):
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
        raise InterpolationSyntaxError(
            'Empty expression ("${}" or "${...:+}") is not a supported environment variable interpolation syntax.'
        )
    elif contents == "$":
        return "$"
    elif root and (contents.startswith("$") or contents.startswith("/")):
        return _get_ref_string(root, contents)
    elif contents.startswith("&") and contents.endswith(";"):
        return unescape(contents)
    else:
        return _get_env_var_string(root, contents)


def round_sub(root: Root, *, contents: str) -> str:
    warnings.warn("`!Sub $()` is reserved", InterpolationWarning, stacklevel=1)
    return "$(" + contents + ")"


SUB_PATTERNS: typ.Final[tabc.Sequence[tuple[tabc.Callable, re.Pattern[str]]]] = (
    (round_sub, re.compile(r"(\$\((?P<contents>.*?)\))")),
    (curly_sub, re.compile(r"(\$\{(?P<contents>.*?)\})")),
)


def _replacer(sub: tabc.Callable, root: Root, match: re.Match[str]) -> str:
    return sub(root, **match.groupdict())


def interpolate(value: str, root: Root) -> str:
    for sub, pat in SUB_PATTERNS:
        value = pat.sub(partial(_replacer, sub, root), value)
    return value


# Trying to explain with variable names
DOLLAR_BUT_NOT_END = r"\$(?!\})"
SLASH = r"/"
DOLLAR_OR_SLASH = f"(?:{DOLLAR_BUT_NOT_END}|{SLASH})"
NESTING = r".+?\:\+"
NESTING_DOLLAR_OR_SLASH = NESTING + DOLLAR_OR_SLASH
STARTS_WITH_OR_NESTING_DOLLAR_OR_SLASH = f"(?:{DOLLAR_OR_SLASH}|{NESTING_DOLLAR_OR_SLASH})"
DOLLAR_BRACKET = r"\$\{"
WHOLE_THING = DOLLAR_BRACKET + STARTS_WITH_OR_NESTING_DOLLAR_OR_SLASH
# WHOLE_THING = r"\$\{(?:(?:\$(?!\})|/)|.+?\:\+(?:\$(?!\})|/))"

DOES_REF_PATTERN = re.compile(WHOLE_THING)

del (
    DOLLAR_BUT_NOT_END,
    SLASH,
    DOLLAR_OR_SLASH,
    NESTING,
    NESTING_DOLLAR_OR_SLASH,
    STARTS_WITH_OR_NESTING_DOLLAR_OR_SLASH,
    DOLLAR_BRACKET,
    WHOLE_THING,
)  # Clean up all those temporary variables


def interpolation_needs_ref_condition(value: str) -> bool:
    """
    A ``needs_root_condition`` usable by :py:func:`.as_lazy_with_root`.

    Works with :py:func:`.interpolate_value_with_ref` to check if ``value`` uses a JSON Path or JSON Pointer interpolation.

    Used by :ref:`tag-sub`.

    :param str value: Unprocessed YAML str
    :return: :py:data:`True`, if the value contains an interpolation that uses JSON Path or Pointer
    :rtype: bool
    """

    return bool(DOES_REF_PATTERN.search(value))


def interpolate_value_with_ref(
    func: tabc.Callable[typ.Concatenate[str, Root, P], RT],
    /,
) -> tabc.Callable[typ.Concatenate[str, Root, P], RT]:
    """Replaces the YAML string value with the interpolated value before calling the tag function

    "with_ref" does full interpolation, supporting references (e.g. ``${$.value}`` and ``${/value}``).

    .. admonition:: Compatible Laziness Decorators
        :class: caution

        - :py:func:`.as_lazy_with_root`
        - :py:func:`.as_lazy_with_root_and_load_options`

    :param ~collections.abc.Callable[~typing.Concatenate[str, ~granular_configuration_language.yaml.classes.Root, P], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[~typing.Concatenate[str, ~granular_configuration_language.yaml.classes.Root, P], RT]

    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_lazy_with_root
            @interpolate_value_with_ref
            def tag(value: str, root: Root) -> Any:
                ...

            @string_tag(Tag("!Tag"))
            @as_lazy_with_root_and_load_options
            @interpolate_value_with_ref
            def tag_with_options(value: str, root: Root, options: LoadOptions) -> Any:
                ...
    """

    @tracker.wraps(func, is_with_ref=True)
    def lazy_wrapper(value: str, root: Root, /, *args: P.args, **kwargs: P.kwargs) -> RT:
        return func(interpolate(value, root), root, *args, **kwargs)

    return lazy_wrapper


def interpolate_value_without_ref(
    func: tabc.Callable[typ.Concatenate[str, P], RT],
    /,
) -> tabc.Callable[typ.Concatenate[str, P], RT]:
    """Replaces the YAML string value with the interpolated value before calling the tag function

    "without_ref" does a limited interpolation that does not support references (e.g. ``${$.value}`` and ``${/value}``)

    .. admonition:: Compatible Laziness Decorators
        :class: caution

        - :py:func:`.as_lazy`
        - :py:func:`.as_lazy_with_root`
        - :py:func:`.as_lazy_with_root_and_load_options`

    :param ~collections.abc.Callable[~typing.Concatenate[str, P], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[~typing.Concatenate[str, P], RT]

    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_lazy
            @interpolate_value_with_ref
            def tag(value: str) -> Any:
                ...


            @string_tag(Tag("!Tag"))
            @as_lazy_with_load_options
            @interpolate_value_with_ref
            def tag_with_options(value: str, options: LoadOptions) -> Any:
                ...

    """

    @tracker.wraps(func, is_without_ref=True)
    def lazy_wrapper(value: str, /, *args: P.args, **kwargs: P.kwargs) -> RT:
        return func(interpolate(value, None), *args, **kwargs)

    return lazy_wrapper


def interpolate_value_eager_io(
    func: tabc.Callable[typ.Concatenate[str, P], RT],
    /,
) -> tabc.Callable[typ.Concatenate[str, P], RT]:
    """Replaces the 1st parameter with the interpolated value before calling the function.

    This version is for Eager IO functions.

    This does a limited interpolation that does not support references (e.g. ``${$.value}`` and ``${/value}``)

    .. admonition:: This is not for Tags functions.
        :class: error

        - This decorator is for functions passed to :py:func:`!.as_eager_io` and :py:func:`!.as_eager_io_with_root_and_load_options`, not wrapped by.
        - For Tags, use :py:func:`.interpolate_value_without_ref`

    :param ~collections.abc.Callable[~typing.Concatenate[str, P], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[~typing.Concatenate[str, P], RT]
    """

    @tracker.wraps(func, is_without_ref=True, fake_tag=True)
    def lazy_wrapper(value: str, /, *args: P.args, **kwargs: P.kwargs) -> RT:
        return func(interpolate(value, None), *args, **kwargs)

    return lazy_wrapper
