from __future__ import annotations

import typing as typ
from pathlib import Path

from granular_configuration_language.yaml.file_loading import as_file_path
from granular_configuration_language.yaml.classes import LazyRoot
from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    as_lazy_with_root_and_load_options,
    interpolate_value_with_ref,
    string_tag,
)


def _load(file: Path, options: LoadOptions, root: Root) -> typ.Any:
    from granular_configuration_language._load import load_file

    lazy_root = LazyRoot.with_root(root)
    return load_file(file, lazy_root=lazy_root, mutable=options.mutable, previous_options=options)


@string_tag(Tag("!ParseFile"), "Parser", sort_as="!ParseFile1")
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
def handler(value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = as_file_path("!ParseFile", value, options)

    return _load(file, options, root)


@string_tag(Tag("!OptionalParseFile"), "Parser", sort_as="!ParseFile2")
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
def handler_optional(value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = as_file_path("!OptionalParseFile", value, options)

    if file.exists():
        return _load(file, options, root)
    else:
        return None
