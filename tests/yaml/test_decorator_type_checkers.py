from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from granular_configuration_language.exceptions import ErrorWhileLoadingTags, TagHadUnsupportArgument
from granular_configuration_language.yaml import loads
from granular_configuration_language.yaml.decorators import Tag, string_tag


def test_string_tag_does_not_take_sequence() -> None:
    with pytest.raises(TagHadUnsupportArgument):
        loads("!Mask []")


def test_string_tag_does_not_take_mapping() -> None:
    with pytest.raises(TagHadUnsupportArgument):
        loads("!Mask {}")


def test_string_or_twople_tag_only_takes_two_or_one() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(TagHadUnsupportArgument):
            loads("""!ParseEnv ["a", "b", "c"]""")


def test_string_or_twople_tag_does_not_take_mapping() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(TagHadUnsupportArgument):
            loads('!ParseEnv {"unreal_env_vari": 1}')


def test_string_or_twople_tag_dooes_not_take_an_empty_sequence() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(TagHadUnsupportArgument):
            loads("""!ParseEnv []""")


def test_sequence_of_any_tag_does_not_take_scalar() -> None:
    with pytest.raises(TagHadUnsupportArgument):
        loads("!Merge abc")


def test_sequence_of_any_tag_does_not_take_mapping() -> None:
    with pytest.raises(TagHadUnsupportArgument):
        loads("!Merge {}")


def test_mapping_of_any_tag_does_not_take_scalar() -> None:
    with pytest.raises(TagHadUnsupportArgument):
        loads("!Dict abc")


def test_mapping_of_any_tag_does_not_take_sequence() -> None:
    with pytest.raises(TagHadUnsupportArgument):
        loads("!Dict []")


def test_tag_not_starting_with_bang_errors() -> None:
    with pytest.raises(ErrorWhileLoadingTags):
        string_tag(Tag("Test"))
