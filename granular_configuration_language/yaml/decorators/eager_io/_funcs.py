from __future__ import annotations

from granular_configuration_language.yaml.decorators import LoadOptions, Tag
from granular_configuration_language.yaml.decorators.interpolate import interpolate_value_eager_io
from granular_configuration_language.yaml.file_ops import as_file_path
from granular_configuration_language.yaml.file_ops.binary import EagerIOBinaryFile, load_binary_file
from granular_configuration_language.yaml.file_ops.text import EagerIOTextFile, load_text_file


def eager_io_text_loader(value: str, tag: Tag, options: LoadOptions) -> EagerIOTextFile:
    return load_text_file(as_file_path(tag, value, options))


eager_io_text_loader_interpolates = interpolate_value_eager_io(eager_io_text_loader)


def eager_io_binary_loader(value: str, tag: Tag, options: LoadOptions) -> EagerIOBinaryFile:
    return load_binary_file(as_file_path(tag, value, options))


eager_io_binary_loader_interpolates = interpolate_value_eager_io(eager_io_binary_loader)
