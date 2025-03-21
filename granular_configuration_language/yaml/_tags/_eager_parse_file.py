from __future__ import annotations

import typing as typ

from granular_configuration_language.yaml.decorators import LoadOptions, Root, Tag, string_tag
from granular_configuration_language.yaml.decorators.eager_io import (
    EagerIOTextFile,
    as_eager_io,
    as_eager_io_with_root_and_load_options,
    eager_io_text_loader_interpolates,
)
from granular_configuration_language.yaml.file_loading import load_yaml_from_file


def _load_safe(value: str) -> typ.Any:
    from ruamel.yaml import YAML

    return YAML(typ="safe").load(value)


@string_tag(Tag("!EagerParseFile"), "Parser", sort_as="!ParseFile3")
@as_eager_io_with_root_and_load_options(eager_io_text_loader_interpolates)
def handler(value: EagerIOTextFile, root: Root, options: LoadOptions) -> typ.Any:
    return load_yaml_from_file(value, options, root)


@string_tag(Tag("!EagerOptionalParseFile"), "Parser", sort_as="!ParseFile4")
@as_eager_io_with_root_and_load_options(eager_io_text_loader_interpolates)
def handler_optional(value: EagerIOTextFile, root: Root, options: LoadOptions) -> typ.Any:
    if value.exists:
        return load_yaml_from_file(value, options, root)
    else:
        return None


@string_tag(Tag("!EagerSafeParseFile"), "Undoc-ed", sort_as="!ParseFile5")
@as_eager_io(eager_io_text_loader_interpolates)
def handler_safe(value: EagerIOTextFile) -> typ.Any:
    if value.exists:
        return _load_safe(value.data)
    else:
        return None
