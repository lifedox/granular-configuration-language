from __future__ import annotations

import typing as typ
from pathlib import Path

from granular_configuration_language._configuration import Configuration, MutableConfiguration
from granular_configuration_language.yaml.classes import LazyEval, LazyRoot, LoadOptions, StateHolder
from granular_configuration_language.yaml.load._load_yaml_string import load_yaml_string


def loads(
    config_str: str,
    *,
    lazy_root: LazyRoot | None = None,
    file_path: Path | None = None,
    previous_options: LoadOptions | None = None,
    mutable: bool = False,
) -> typ.Any:
    state = StateHolder(
        lazy_root_obj=lazy_root or LazyRoot(),
        options=LoadOptions(
            file_location=file_path,
            relative_to_directory=file_path.parent if file_path is not None else Path(),
            obj_pairs_func=obj_pairs_func(mutable),
            sequence_func=sequence_func(mutable),
            mutable=mutable,
            previous=previous_options,
        ),
    )

    result = load_yaml_string(config_str, state)

    if lazy_root is None:
        state.lazy_root_obj._set_root(result)

    if isinstance(result, LazyEval):
        return result.result
    else:
        return result


def obj_pairs_func(mutable: bool) -> type[Configuration] | type[MutableConfiguration]:
    return MutableConfiguration if mutable else Configuration


def sequence_func(mutable: bool) -> type[list] | type[tuple]:
    return list if mutable else tuple
