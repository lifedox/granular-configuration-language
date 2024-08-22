from __future__ import annotations

import typing as typ
from copy import copy
from functools import partial

from ruamel.yaml import YAML, MappingNode, SafeConstructor
from ruamel.yaml.resolver import BaseResolver

from granular_configuration.yaml._tags import handlers
from granular_configuration.yaml.classes import StateHolder


def construct_mapping(cls: typ.Type, constructor: SafeConstructor, node: MappingNode) -> typ.Mapping:
    node.value = [pair for pair in node.value if pair[0].tag != "!Del"]
    return cls(constructor.construct_mapping(node, deep=True))


def make_constructor_class(state: StateHolder) -> typ.Type[SafeConstructor]:
    class ExtendedSafeConstructor(SafeConstructor):
        yaml_constructors = copy(SafeConstructor.yaml_constructors)

    for handler in handlers:
        handler(ExtendedSafeConstructor, state)

    ExtendedSafeConstructor.add_constructor(
        BaseResolver.DEFAULT_MAPPING_TAG, partial(construct_mapping, state.options.obj_pairs_func)
    )

    return ExtendedSafeConstructor


def load_yaml_string(config_str: str, state: StateHolder) -> typ.Any:
    if config_str.startswith("%YAML"):
        yaml = YAML(typ="rt")
    else:
        yaml = YAML(typ="safe")

    yaml.Constructor = make_constructor_class(state)
    return yaml.load(config_str)
