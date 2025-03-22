from __future__ import annotations

from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Tag,
    as_lazy_with_load_options,
    interpolate_value_without_ref,
    string_tag,
    with_tag,
)
from granular_configuration_language.yaml.decorators.eager_io import (
    EagerIOBinaryFile,
    as_eager_io,
    eager_io_binary_loader_interpolates,
)
from granular_configuration_language.yaml.file_loading import as_file_path, read_binary_data


@string_tag(Tag("!LoadBinary"), "Undoc-ed")
@as_lazy_with_load_options
@interpolate_value_without_ref
@with_tag
def load_binary(tag: Tag, value: str, options: LoadOptions) -> bytes:
    return read_binary_data(as_file_path(tag, value, options))


@string_tag(Tag("!EagerLoadBinary"), "Undoc-ed")
@as_eager_io(eager_io_binary_loader_interpolates)
def eager_load_binary(file: EagerIOBinaryFile) -> bytes:
    return read_binary_data(file)
