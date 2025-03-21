from __future__ import annotations

import typing as typ

from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    as_lazy_with_root_and_load_options,
    interpolate_value_with_ref,
    string_tag,
    with_tag,
)
from granular_configuration_language.yaml.file_loading import as_file_path, load_yaml_from_file


@string_tag(Tag("!ParseFile"), "Parser", sort_as="!ParseFile1")
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
@with_tag
def handler(tag: Tag, value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = as_file_path(tag, value, options)

    return load_yaml_from_file(file, options, root)


@string_tag(Tag("!OptionalParseFile"), "Parser", sort_as="!ParseFile2")
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
@with_tag
def handler_optional(tag: Tag, value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = as_file_path(Tag("!OptionalParseFile"), value, options)

    if file.exists():
        return load_yaml_from_file(file, options, root)
    else:
        return None
