from __future__ import annotations

import typing as typ
from collections.abc import MutableMapping
from copy import copy
from functools import partial
from pathlib import Path

from ruamel.yaml import YAML, MappingNode, SafeConstructor
from ruamel.yaml.resolver import BaseResolver

from granular_configuration.yaml._tags import handlers
from granular_configuration.yaml.classes import _OPH, LazyRoot, LoadOptions, StateHolder


def construct_mapping(cls: typ.Type, constructor: SafeConstructor, node: MappingNode) -> typ.MutableMapping:
    node.value = [pair for pair in node.value if pair[0].tag != "!Del"]
    return cls(constructor.construct_mapping(node, deep=True))


def internal(
    config_str: str,
    obj_pairs_hook: _OPH = None,
    *,
    lazy_root: typ.Optional[LazyRoot] = None,
    file_path: typ.Optional[Path] = None,
) -> typ.Any:
    state = StateHolder(
        lazy_root_obj=lazy_root or LazyRoot(),
        options=LoadOptions(
            file_relative_path=file_path.parent if file_path is not None else Path("."),
            obj_pairs_func=obj_pairs_hook,
        ),
    )

    if config_str.startswith("%YAML"):
        yaml = YAML(typ="rt")
    else:
        yaml = YAML(typ="safe")

    if obj_pairs_hook and issubclass(obj_pairs_hook, MutableMapping):
        oph = obj_pairs_hook
    else:  # pragma: no cover
        oph = dict

    class ExtendedSafeConstructor(SafeConstructor):
        yaml_constructors = copy(SafeConstructor.yaml_constructors)

    for handler in handlers:
        handler(ExtendedSafeConstructor, state)

    ExtendedSafeConstructor.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, partial(construct_mapping, oph))

    yaml.Constructor = ExtendedSafeConstructor

    result = yaml.load(config_str)

    if lazy_root is None:
        state.lazy_root_obj._set_root(result)

    return result
