import typing as typ
from itertools import permutations
from pathlib import Path

from granular_configuration._locations import Locations

ASSET_DIR = (Path(__file__).parent / "assets" / "test_locations").resolve()


def test_assets_are_as_expect() -> None:
    expected = [
        ASSET_DIR / "both.yaml",
        ASSET_DIR / "both.yml",
        ASSET_DIR / "different_ext.txt",
        ASSET_DIR / "just_yaml.yaml",
        ASSET_DIR / "just_yml.yml",
    ]
    assert sorted(ASSET_DIR.iterdir()) == expected


def test_no_file() -> None:
    test = (ASSET_DIR / "no_file.yaml",)
    expected: typ.Sequence[Path] = tuple()
    assert tuple(Locations(test)) == expected


def test_single_file() -> None:
    test = (ASSET_DIR / "just_yaml.yaml",)
    expected = (ASSET_DIR / "just_yaml.yaml",)
    assert tuple(Locations(test)) == expected


def test_two_files() -> None:
    test = (
        ASSET_DIR / "just_yaml.yaml",
        ASSET_DIR / "different_ext.txt",
    )
    expected = (
        ASSET_DIR / "just_yaml.yaml",
        ASSET_DIR / "different_ext.txt",
    )
    assert tuple(Locations(test)) == expected


def test_star_select() -> None:
    test = (
        ASSET_DIR / "just_yaml.*",
        ASSET_DIR / "just_yml.*",
        ASSET_DIR / "both.*",
        ASSET_DIR / "different_ext.*",
    )
    expected = (
        ASSET_DIR / "just_yaml.yaml",
        ASSET_DIR / "just_yml.yml",
        ASSET_DIR / "both.yaml",
    )
    assert tuple(Locations(test)) == expected


def test_ystar_select() -> None:
    test = (
        ASSET_DIR / "just_yaml.y*",
        ASSET_DIR / "just_yml.y*",
        ASSET_DIR / "both.y*",
        ASSET_DIR / "different_ext.y*",
    )
    expected = (
        ASSET_DIR / "just_yaml.yaml",
        ASSET_DIR / "just_yml.yml",
        ASSET_DIR / "both.yaml",
    )
    assert tuple(Locations(test)) == expected


def test_yml_select() -> None:
    test = (
        ASSET_DIR / "just_yaml.yml",
        ASSET_DIR / "just_yml.yml",
        ASSET_DIR / "both.yml",
        ASSET_DIR / "different_ext.yml",
    )
    expected = (
        ASSET_DIR / "just_yaml.yaml",
        ASSET_DIR / "just_yml.yml",
        ASSET_DIR / "both.yaml",
    )
    assert tuple(Locations(test)) == expected


def test_equality_of_star() -> None:
    assert Locations((ASSET_DIR / "A.*",)) == Locations((ASSET_DIR / "A.y*",))


def test_equality_of_star_expansion_is_differnt_then_individual() -> None:
    assert Locations((ASSET_DIR / "A.*",)) != Locations((ASSET_DIR / "A.yaml", ASSET_DIR / "A.yml"))


def test_equality_of_mix() -> None:
    test = (ASSET_DIR / "A.*", ASSET_DIR / "B.y*", ASSET_DIR / "C.yaml")

    cases = permutations(test)

    assert Locations(test) == Locations(next(cases))

    for case in cases:
        assert Locations(test) != Locations(case)
