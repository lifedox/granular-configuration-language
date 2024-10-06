from __future__ import annotations

import typing as typ

from granular_configuration_language._config import Configuration
from granular_configuration_language.yaml.decorators._base import TagDecoratorBase


class string_tag(TagDecoratorBase[str]):
    Type: typ.TypeAlias = str

    @property
    def user_friendly_type(self) -> str:
        return "str"

    def scalar_node_type_check(self, value: str) -> typ.TypeGuard[Type]:
        return True


class string_or_twople_tag(TagDecoratorBase[str | tuple[str, typ.Any]]):
    Type: typ.TypeAlias = str | tuple[str, typ.Any]

    @property
    def user_friendly_type(self) -> str:
        return "str | tuple[str, Any]"

    def scalar_node_type_check(self, value: str) -> typ.TypeGuard[str]:
        return True

    def sequence_node_type_check(self, value: typ.Sequence) -> typ.TypeGuard[tuple[str, typ.Any]]:
        return (len(value) == 2) and isinstance(value[0], str)

    def sequence_node_transformer(self, value: typ.Any) -> Type:
        return tuple(value)


class sequence_of_any_tag(TagDecoratorBase[typ.Sequence[typ.Any]]):
    Type: typ.TypeAlias = typ.Sequence[typ.Any]

    @property
    def user_friendly_type(self) -> str:
        return "list[Any]"

    def sequence_node_type_check(self, value: typ.Sequence) -> typ.TypeGuard[Type]:
        return True


class mapping_of_any_tag(TagDecoratorBase[Configuration]):
    Type: typ.TypeAlias = Configuration

    @property
    def user_friendly_type(self) -> str:
        return "dict[Any, Any]"

    def mapping_node_type_check(self, value: typ.Mapping) -> typ.TypeGuard[Type]:
        return True
