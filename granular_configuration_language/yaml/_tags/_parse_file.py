from __future__ import annotations

import typing as typ
from pathlib import Path

from granular_configuration_language.yaml._parsing import is_in_chain, make_chain_message
from granular_configuration_language.yaml.classes import LazyRoot
from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    as_lazy_with_root_and_load_options,
    interpolate_value_with_ref,
    string_tag,
)


def _as_file_path(tag: str, value: str, options: LoadOptions) -> Path:
    result = options.relative_to_directory / value

    if is_in_chain(result, options):
        raise make_chain_message(tag, value, options)

    return result


def _load(file: Path, options: LoadOptions, root: Root) -> typ.Any:
    from granular_configuration_language._load import load_file

    lazy_root = LazyRoot.with_root(root)
    output = load_file(file, lazy_root=lazy_root, mutable=options.mutable, previous_options=options)
    return output


@string_tag(Tag("!ParseFile"), "Parser")
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
def handler(value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = _as_file_path("!ParseFile", value, options)

    return _load(file, options, root)


@string_tag(Tag("!OptionalParseFile"), "Parser", sort_as="!ParseFile1")
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
def handler_optional(value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = _as_file_path("!OptionalParseFile", value, options)

    if file.exists():
        return _load(file, options, root)
    else:
        return None
