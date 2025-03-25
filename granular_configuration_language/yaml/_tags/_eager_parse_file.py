from __future__ import annotations

import typing as typ

from granular_configuration_language.yaml.decorators import LoadOptions, Root, Tag, string_tag
from granular_configuration_language.yaml.decorators.eager_io import (
    EagerIOTextFile,
    as_eager_io_with_root_and_load_options,
    eager_io_text_loader_interpolates,
)
from granular_configuration_language.yaml.file_ops.yaml import load_from_file


@string_tag(Tag("!EagerParseFile"), "Parser", sort_as="!ParseFile3")
@as_eager_io_with_root_and_load_options(eager_io_text_loader_interpolates)
def handler(value: EagerIOTextFile, root: Root, options: LoadOptions) -> typ.Any:
    return load_from_file(value, options, root)


@string_tag(Tag("!EagerOptionalParseFile"), "Parser", sort_as="!ParseFile4")
@as_eager_io_with_root_and_load_options(eager_io_text_loader_interpolates)
def handler_optional(value: EagerIOTextFile, root: Root, options: LoadOptions) -> typ.Any:
    if value.exists:
        return load_from_file(value, options, root)
    else:
        return None
