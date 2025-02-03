import collections.abc as tabc
import typing as typ

from ruamel.yaml import MappingNode, SafeConstructor, SequenceNode

from granular_configuration_language.yaml.classes import LazyEval


def construct_mapping(cls: typ.Type, constructor: SafeConstructor, node: MappingNode) -> tabc.Mapping:
    node.value = [pair for pair in node.value if pair[0].tag != "!Del"]

    value: tabc.Mapping = cls(constructor.construct_mapping(node, deep=False))

    for key in value.keys():
        if isinstance(key, LazyEval):
            raise TypeError("Lazy Tags are not allowed as keys to mappings.")

    return cls(constructor.construct_mapping(node, deep=False))


def construct_sequence(cls: typ.Type, constructor: SafeConstructor, node: SequenceNode) -> tabc.Sequence:
    value = constructor.construct_sequence(node, deep=False)

    if isinstance(value, cls):
        return value
    else:
        return cls(value)
