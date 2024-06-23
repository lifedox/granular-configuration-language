import typing as typ
from pathlib import Path

from granular_configuration.yaml.classes import LazyRoot
from granular_configuration.yaml.decorators import Root, StateOptions, Tag, make_lazy_root_with_state, string_tag
from granular_configuration.yaml.ytags.sub import interpolate


def interpolate_value(value: str, options: StateOptions, root: Root) -> Path:
    return options.file_relative_path / interpolate(value, root)


def load(file: Path, state: StateOptions, root: Root) -> typ.Any:
    from granular_configuration._load import load_file

    lazy_root = LazyRoot()
    lazy_root._set_root(root)
    output = load_file(file, obj_pairs_hook=state.obj_pairs_func, lazy_root=lazy_root)
    return output


@string_tag(Tag("!ParseFile"))
@make_lazy_root_with_state
def handler(value: str, options: StateOptions, root: Root) -> typ.Any:
    file = interpolate_value(value, options, root)

    return load(file, options, root)


@string_tag(Tag("!OptionalParseFile"))
@make_lazy_root_with_state
def handler_optional(value: str, options: StateOptions, root: Root) -> typ.Any:
    file = interpolate_value(value, options, root)

    if file.exists():
        return load(file, options, root)
    else:
        return (options.obj_pairs_func or dict)()
