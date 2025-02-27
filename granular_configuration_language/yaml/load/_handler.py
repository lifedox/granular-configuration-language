from __future__ import annotations

import typing as typ
from copy import copy
from functools import partial

from ruamel.yaml import YAML, SafeConstructor
from ruamel.yaml.resolver import BaseResolver

from granular_configuration_language.yaml._tags import handlers
from granular_configuration_language.yaml.classes import StateHolder
from granular_configuration_language.yaml.load._constructors import construct_mapping, construct_sequence


def make_constructor_class(state: StateHolder) -> type[SafeConstructor]:
    class ExtendedSafeConstructor(SafeConstructor):
        yaml_constructors = copy(SafeConstructor.yaml_constructors)

    for handler in handlers:
        handler(ExtendedSafeConstructor, state)

    ExtendedSafeConstructor.add_constructor(
        BaseResolver.DEFAULT_MAPPING_TAG, partial(construct_mapping, state.options.obj_pairs_func)
    )
    ExtendedSafeConstructor.add_constructor(
        BaseResolver.DEFAULT_SEQUENCE_TAG, partial(construct_sequence, state.options.sequence_func)
    )

    return ExtendedSafeConstructor


def load_yaml_string(config_str: str, state: StateHolder) -> typ.Any:
    if config_str.startswith("%YAML"):
        yaml = YAML(typ="rt")
    else:
        yaml = YAML(typ="safe")

    yaml.Constructor = make_constructor_class(state)
    return yaml.load(config_str)
