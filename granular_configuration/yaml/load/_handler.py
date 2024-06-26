from __future__ import annotations

import typing as typ
from collections.abc import MutableMapping
from copy import copy
from functools import partial
from pathlib import Path

from ruamel.yaml import YAML, MappingNode, Node, SafeConstructor
from ruamel.yaml.resolver import BaseResolver

from granular_configuration.yaml.classes import LazyEval, LazyRoot, LoadOptions, StateHolder
from granular_configuration.yaml.ytags import handlers

_OPH = typ.Optional[typ.Type[MutableMapping]]


if typ.TYPE_CHECKING:  # pragma: no cover

    class ExtendedSafeConstructor(SafeConstructor):
        pass


def construct_mapping(cls: typ.Type, constructor: ExtendedSafeConstructor, node: Node) -> typ.MutableMapping:
    if isinstance(node, MappingNode):
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
    else:
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


def external(
    config_str: str,
    obj_pairs_hook: _OPH = None,
    *,
    lazy_root: typ.Optional[LazyRoot] = None,
    file_path: typ.Optional[Path] = None,
) -> typ.Any:
    result = internal(config_str, obj_pairs_hook=obj_pairs_hook, lazy_root=lazy_root, file_path=file_path)
    if isinstance(result, LazyEval):
        return result.result
    else:
        return result