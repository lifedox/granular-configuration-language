from __future__ import annotations

import typing as typ

from granular_configuration_language._configuration import Configuration
from granular_configuration_language.yaml.decorators._base import TagDecoratorBase


class string_tag(TagDecoratorBase[str]):
    """
    A decorator factory for Tags that take a YAML string as argument.

    Example:
    ```python
    @string_tag(Tag("!Tag"))
    @as_lazy
    def tag(value: str) -> Any:
        ...
    ```
    """

    Type: typ.TypeAlias = str
    """
    TypeAlias for this Tag factory
    """

    @property
    def user_friendly_type(self) -> str:
        return "str"

    def scalar_node_type_check(self, value: str) -> typ.TypeGuard[Type]:
        return True


class string_or_twople_tag(TagDecoratorBase[str | tuple[str, typ.Any]]):
    """
    A decorator factory for Tags that take a YAML string or tuple of a YAML strings and YAML object as argument.

    Example:
    ```python
    @string_or_twople_tag(Tag("!Tag"))
    @as_lazy
    def tag(value: string_or_twople_tag.Type) -> Any:
        ...
    ```
    """

    Type: typ.TypeAlias = str | tuple[str, typ.Any]
    """
    TypeAlias for this Tag factory
    """

    @property
    def user_friendly_type(self) -> str:
        return "str | tuple[str, Any]"

    def scalar_node_type_check(self, value: str) -> typ.TypeGuard[str]:
        return True

    def sequence_node_type_check(self, value: typ.Sequence) -> typ.TypeGuard[tuple[str, typ.Any]]:
        return (1 <= len(value) <= 2) and isinstance(value[0], str)

    def sequence_node_transformer(self, value: typ.Any) -> Type:
        if len(value) == 2:
            return value
        else:
            return value[0]


class sequence_of_any_tag(TagDecoratorBase[typ.Sequence[typ.Any]]):
    """
    A decorator factory for Tags that take a YAML sequence as argument.

    Example:
    ```python
    @sequence_of_any_tag(Tag("!Tag"))
    @as_lazy
    def tag(value: Sequence[Any]) -> Any:
        ...
    ```
    """

    Type: typ.TypeAlias = typ.Sequence[typ.Any]
    """
    TypeAlias for this Tag factory
    """

    @property
    def user_friendly_type(self) -> str:
        return "list[Any]"

    def sequence_node_type_check(self, value: typ.Sequence) -> typ.TypeGuard[Type]:
        return True


class mapping_of_any_tag(TagDecoratorBase[Configuration]):
    """
    A decorator factory for Tags that take a YAML mapping as argument.

    Example:
    ```python
    @mapping_of_any_tag(Tag("!Tag"))
    @as_lazy
    def tag(value: Configuration) -> Any:
        ...
    ```
    """

    Type: typ.TypeAlias = Configuration
    """
    TypeAlias for this Tag factory
    """

    @property
    def user_friendly_type(self) -> str:
        return "dict[Any, Any]"

    def mapping_node_type_check(self, value: typ.Mapping) -> typ.TypeGuard[Type]:
        return True
