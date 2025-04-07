from __future__ import annotations

import collections.abc as tabc
import re
import sys
import typing
from unittest.mock import patch

import pytest

from granular_configuration_language.exceptions import TagHadUnsupportArgument
from granular_configuration_language.yaml import loads
from granular_configuration_language.yaml.decorators import Tag, TagDecoratorBase, as_lazy
from granular_configuration_language.yaml.decorators._tag_set import TagSet

if sys.version_info >= (3, 12):
    from typing import override
elif typing.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func


class float_tag(TagDecoratorBase[float]):
    Type: typing.TypeAlias = float

    @property
    def user_friendly_type(self) -> str:
        return "float"

    @override
    def scalar_node_type_check(
        self,
        value: str,
    ) -> typing.TypeGuard[float]:
        """"""  # Make undocumented
        try:
            float(value)
            return True
        except ValueError:
            return False

    @override
    def scalar_node_transformer(
        self,
        value: typing.Any,
    ) -> float:
        """"""  # Make undocumented
        return float(value)


class float_tag_varient(float_tag):
    @override
    def scalar_node_type_check(
        self,
        value: typing.Any,
    ) -> typing.TypeGuard[float]:
        return True


@float_tag(Tag("!Double"), "Typer")
@as_lazy
def double(value: float) -> float:
    return value * 2.0


@float_tag_varient(Tag("!Halve"), "Typer")
@as_lazy
def halve(value: float) -> float:
    return value / 2.0


@patch("granular_configuration_language.yaml._tags.handlers", TagSet((double, halve)))
class TestPatched:

    def test_double_tag_can_double_4_25_to_8_5(self) -> None:
        assert loads("!Double 4.25") == 8.5

    def test_double_tag_fails(self) -> None:
        with pytest.raises(
            TagHadUnsupportArgument,
            match=re.escape("`!Double` supports: float. Got: `ScalarNode(tag='!Double', value='number')`"),
        ):
            loads("!Double number")

    def test_halve_tag_can_halve_8_5_to_4_25(self) -> None:
        assert loads("!Halve 8.5") == 4.25

    def test_halve_tag_fails(self) -> None:
        with pytest.raises(
            TagHadUnsupportArgument,
            match=re.escape("`!Halve` supports: float. Got: `ScalarNode(tag='!Halve', value='number')`"),
        ):
            loads("!Halve number")
