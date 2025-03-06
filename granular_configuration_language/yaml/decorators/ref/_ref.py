from __future__ import annotations

import collections.abc as tabc
import operator as op
import re
import typing as typ

import jsonpath

from granular_configuration_language.exceptions import (
    JSONPathOnlyWorksOnMappings,
    JSONPathQueryFailed,
    JSONPointerQueryFailed,
    RefMustStartFromRoot,
)
from granular_configuration_language.yaml.classes import LazyEval
from granular_configuration_language.yaml.decorators import Root

SUB_PATTERN: re.Pattern[str] = re.compile(r"(\$\{(?P<contents>.*?)\})")


def _resolve_pointer(query: str, root: tabc.Mapping) -> typ.Any:
    try:
        not_found = object()

        result = jsonpath.JSONPointer(query).resolve(root, default=not_found)

        if result is not_found:
            raise JSONPointerQueryFailed(f"JSON Pointer `{query}` did not find a match.")
        else:
            return result

    except RecursionError:
        raise RecursionError(
            (
                f"JSON Pointer `{query}` caused a recursion error. Please check your configuration for a self-referencing loop."
            )
        ) from None


def _resolve_path(query: str, root: tabc.Mapping) -> typ.Any:
    try:
        result = tuple(map(op.attrgetter("value"), jsonpath.finditer(query, root)))

        if len(result) == 1:
            return result[0]
        elif len(result) == 0:
            raise JSONPathQueryFailed(f"JSON Path `{query}` did not find a match.")
        else:
            return result

    except RecursionError:
        raise RecursionError(
            (
                f"JSON Path `{query}` caused a recursion error. Please check your configuration for a self-referencing loop."
            )
        ) from None


def resolve_json_ref(query: str, root: Root) -> typ.Any:
    """
    Queries ``Root`` using JSON Pointer or JSON Path

    .. admonition:: JSON Path
        :class: note
        :collapsible: closed

        - JSON Path can be used to be a pointer to data or a constructor from data.
        - If the query matches one item, then that one item is returned.
        - If the query matches more than one item, that a :py:class:`tuple` of items is returned.

    :param str query:
        - Starts with ``$`` for a JSON Path query
        - Starts with ``/`` for a JSON Pointer
    :param Root root:
        :py:class:`~collections.abc.Mapping` being queried
    :raises JSONPathOnlyWorksOnMappings: Raised if ``root`` is not a :py:class:`~collections.abc.Mapping`
    :raises RefMustStartFromRoot: Raised if the ``query`` does not start with ``$`` or ``/``.
    :return: Result of the query
    :rtype: ~typing.Any
    """

    if isinstance(root, LazyEval) and root.tag == "!Merge":  # pyright: ignore[reportUnnecessaryIsInstance]
        raise RecursionError(
            f"JSON Query `{query}` attempted recursion. Please check your configuration for a self-referencing loop."
        )
    elif not isinstance(root, tabc.Mapping):
        raise JSONPathOnlyWorksOnMappings(f"JSONPath `{query}` was tried on `{repr(root)}`")
    elif query.startswith("$"):
        return _resolve_path(query, root)
    elif query.startswith("/"):
        return _resolve_pointer(query, root)
    else:
        raise RefMustStartFromRoot(f"JSON query `{query}` must start with '$' for JSON Path or '/' for JSON Pointer")
