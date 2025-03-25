from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from granular_configuration_language import LazyLoadConfiguration
from granular_configuration_language.exceptions import ParsingTriedToCreateALoop
from granular_configuration_language.yaml import loads
from granular_configuration_language.yaml.file_ops import create_environment_variable_path
from granular_configuration_language.yaml.file_ops._chain import stringify_source_chain

ASSET_DIR = (Path(__file__).parent / "../assets/" / "merging_and_parsefile").resolve()


def test_parsefile_and_parseenv_can_fail_together_in_a_loop_starting_with_a_file() -> None:
    env = dict(
        VAR1="!ParseEnv VAR2",
        VAR2="!ParseEnv VAR3",
        VAR3="!ParseFile " + (ASSET_DIR / "parsefile_chain" / "up/1.yaml").resolve().__str__(),
    )

    with patch.dict(os.environ, values=env):
        with pytest.raises(ParsingTriedToCreateALoop):
            loads("!ParseEnv VAR1").next.next.bad


def test_parsefile_and_parseenv_can_fail_together_in_a_loop_starting_with_a_var() -> None:
    env = dict(
        VAR1="!ParseEnv VAR2",
        VAR2="!ParseEnv VAR3",
        VAR3="!ParseFile " + (ASSET_DIR / "parsefile_chain" / "up/1.yaml").resolve().__str__(),
    )
    with patch.dict(os.environ, values=env):
        with pytest.raises(ParsingTriedToCreateALoop):

            config = LazyLoadConfiguration(ASSET_DIR / "parsefile_chain" / "up/1.yaml").config
            config.next.next.bad_env


def test_stringify_source_chain_singles() -> None:
    cwd = Path().resolve()

    assert stringify_source_chain((cwd / "parsefile_itself.yaml",)) == "parsefile_itself.yaml→..."
    assert stringify_source_chain((create_environment_variable_path("VAR"),)) == "$VAR→..."


def test_stringify_source_chain_multiples() -> None:
    cwd = Path().resolve()

    files = (
        cwd / "1.yaml",
        cwd / "2.yaml",
        cwd / "3.yaml",
    )
    vars = (
        create_environment_variable_path("VAR1"),
        create_environment_variable_path("VAR2"),
        create_environment_variable_path("VAR3"),
    )

    assert stringify_source_chain(files) == "1.yaml→2.yaml→3.yaml→..."
    assert stringify_source_chain(vars) == "$VAR1→$VAR2→$VAR3→..."
    assert stringify_source_chain(files + vars) == "1.yaml→2.yaml→3.yaml→$VAR1→$VAR2→$VAR3→..."
    assert stringify_source_chain(vars + files) == "$VAR1→$VAR2→$VAR3→1.yaml→2.yaml→3.yaml→..."


def test_stringify_source_chain_complex() -> None:
    cwd = Path().resolve()

    assert (
        stringify_source_chain(
            (
                cwd / "1.yaml",
                cwd.parent / "1.yaml",
            )
        )
        == "1.yaml→../1.yaml→..."
    )

    assert (
        stringify_source_chain(
            (
                Path("A://a/1.yaml"),
                Path("B://b/2.yaml"),
                Path("C://c/3.yaml"),
            )
        )
        == "1.yaml→2.yaml→3.yaml→..."
    )

    assert (
        stringify_source_chain(
            (
                Path("A://a/1.yaml"),
                Path("B://b/1.yaml"),
                Path("C://c/1.yaml"),
            )
        )
        == "1.yaml→?/1.yaml→?/1.yaml→..."
    )
