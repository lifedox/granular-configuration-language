import typing as typ

from ruamel.yaml import MappingNode, SafeConstructor, SequenceNode


def construct_mapping(cls: typ.Type, constructor: SafeConstructor, node: MappingNode) -> typ.Mapping:
    node.value = [pair for pair in node.value if pair[0].tag != "!Del"]
    return cls(constructor.construct_mapping(node, deep=False))


def construct_sequence(cls: typ.Type, constructor: SafeConstructor, node: SequenceNode) -> typ.Sequence:
    value = constructor.construct_sequence(node, deep=False)

    if isinstance(value, cls):
        return value
    else:
        return cls(value)
