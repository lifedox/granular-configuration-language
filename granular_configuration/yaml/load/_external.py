import typing as typ
from pathlib import Path

from granular_configuration._config import Configuration, MutableConfiguration
from granular_configuration.yaml.classes import LazyEval, LazyRoot, LoadOptions, StateHolder
from granular_configuration.yaml.load._handler import load_yaml_string


def loads(
    config_str: str,
    *,
    lazy_root: typ.Optional[LazyRoot] = None,
    file_path: typ.Optional[Path] = None,
    mutable: bool = False,
) -> typ.Any:
    state = StateHolder(
        lazy_root_obj=lazy_root or LazyRoot(),
        options=LoadOptions(
            file_location=file_path,
            relative_to_directory=file_path.parent if file_path is not None else Path("."),
            obj_pairs_func=obj_pairs_func(mutable),
            mutable=mutable,
        ),
    )

    result = load_yaml_string(config_str, state)

    if lazy_root is None:
        state.lazy_root_obj._set_root(result)

    if isinstance(result, LazyEval):
        return result.result
    else:
        return result


def obj_pairs_func(mutable: bool) -> typ.Type[Configuration] | typ.Type[MutableConfiguration]:
    return MutableConfiguration if mutable else Configuration
