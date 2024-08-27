import typing as typ
from pathlib import Path

from granular_configuration.yaml.classes import LazyRoot
from granular_configuration.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    as_lazy_with_root_and_load_options,
    interpolate_value_with_ref,
    string_tag,
)


def as_file_path(value: str, options: LoadOptions) -> Path:
    return options.relative_to_directory / value


def load(file: Path, option: LoadOptions, root: Root) -> typ.Any:
    from granular_configuration._load import load_file

    lazy_root = LazyRoot.with_root(root)
    output = load_file(file, lazy_root=lazy_root, mutable=option.mutable)
    return output


@string_tag(Tag("!ParseFile"))
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
def handler(value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = as_file_path(value, options)

    return load(file, options, root)


@string_tag(Tag("!OptionalParseFile"))
@as_lazy_with_root_and_load_options
@interpolate_value_with_ref
def handler_optional(value: str, root: Root, options: LoadOptions) -> typ.Any:
    file = as_file_path(value, options)

    if file.exists():
        return load(file, options, root)
    else:
        return options.obj_pairs_func()
