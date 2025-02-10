from __future__ import annotations

import typing as typ


class ParsedEnvironmentVariableSyntax(typ.NamedTuple):
    mode: str | None
    name: slice
    value: slice
    next: int


default_slices = ParsedEnvironmentVariableSyntax("", slice(None, None), slice(None, None), 0)


def _get_mode(value: str, index: int) -> str | None:
    try:
        return value[index]
    except IndexError:
        return None


def get_parser_from_index(value: str, start_index: int) -> ParsedEnvironmentVariableSyntax:
    colon_index = value.find(":", start_index)

    if colon_index < 0:
        return default_slices
    else:
        return ParsedEnvironmentVariableSyntax(
            _get_mode(value, colon_index + 1),
            slice(None, colon_index),
            slice(colon_index + 2, None),
            colon_index + 2,
        )


def parse_environment_variable_syntax(contents: str) -> ParsedEnvironmentVariableSyntax:
    parser = get_parser_from_index(contents, 0)

    while parser.mode == ":":
        parser = get_parser_from_index(contents, parser.next)

    return parser
