import operator as op
import typing as typ
from pathlib import Path
from unittest.mock import patch

import pytest

from granular_configuration._locations import (
    ConfigurationFiles,
    ConfigurationMultiNamedFiles,
    get_all_unique_locations,
    parse_location,
)

ASSET_DIR = (Path(__file__).parent / "../assets/config_location_test").resolve()

DIRECTORIES = (
    ASSET_DIR / "a/b",
    ASSET_DIR / "a",
    ASSET_DIR / "b",
    ASSET_DIR / "c",
    ASSET_DIR / "d",
    ASSET_DIR / "c",
)
FILES = (
    ASSET_DIR / "g/b.yaml",
    ASSET_DIR / "g/h.yaml",
)
FILENAMES = (
    "t.yaml",
    "t2.yaml",
)
EXISTS = (
    ASSET_DIR / "g/h.yaml",
    ASSET_DIR / "a/b/t2.yaml",
    ASSET_DIR / "c/t.yaml",
    ASSET_DIR / "c/t2.yaml",
)


def test_assets_files_exist() -> None:
    assert all(map(op.methodcaller("is_file"), EXISTS)), "Someone removed test assets"


def test__get_files_from_locations() -> None:
    directories = DIRECTORIES
    filenames = FILENAMES
    files = FILES

    exists = EXISTS

    locations = (
        ConfigurationMultiNamedFiles(filenames, directories).get_locations() | ConfigurationFiles(files).get_locations()
    )

    assert sorted(locations) == sorted(exists[:3])


def test__get_files_from_locations_no_filename() -> None:
    directories = DIRECTORIES
    filenames: typ.Tuple[str, ...] = tuple()
    files = FILES

    exists = (ASSET_DIR / "g/h.yaml",)

    locations = (
        ConfigurationMultiNamedFiles(filenames, directories).get_locations() | ConfigurationFiles(files).get_locations()
    )

    assert sorted(locations) == sorted(exists)


def test__get_files_from_locations_no_dirs() -> None:
    directories: typ.Tuple[Path, ...] = tuple()
    filenames = FILENAMES
    files = FILES

    exists = (ASSET_DIR / "g/h.yaml",)

    locations = (
        ConfigurationMultiNamedFiles(filenames, directories).get_locations() | ConfigurationFiles(files).get_locations()
    )

    assert sorted(locations) == sorted(exists)


def test__ConfigurationFiles() -> None:
    files = (
        ASSET_DIR / "placeholder_test1.yaml",
        ASSET_DIR / "placeholder_test2.yaml",
    )
    assert tuple(ConfigurationFiles(files).get_locations()) == files


def test__ConfigurationFiles_from_args() -> None:
    files = (
        ASSET_DIR / "placeholder_test1.yaml",
        ASSET_DIR / "placeholder_test2.yaml",
    )

    assert tuple(ConfigurationFiles.from_args(*files).get_locations()) == files


def test__ConfigurationMultiNamedFiles() -> None:
    directories = DIRECTORIES
    filenames = ("t2.yaml",)

    exists = (
        ASSET_DIR / "a/b/t2.yaml",
        ASSET_DIR / "c/t2.yaml",
    )

    assert tuple(ConfigurationMultiNamedFiles(filenames=filenames, directories=directories).get_locations()) == exists


def test_get_all_unique_locations() -> None:
    directories = DIRECTORIES
    filenames = FILENAMES
    files = FILES

    exists = EXISTS

    from_files = ConfigurationFiles(files=files)
    from_priority = ConfigurationMultiNamedFiles(filenames=filenames, directories=directories)

    assert (
        tuple(
            get_all_unique_locations(
                (
                    from_files,
                    from_priority,
                    from_files,
                )
            )
        )
        == exists[:3]
    )
    assert (
        tuple(
            get_all_unique_locations(
                (
                    from_files,
                    from_priority,
                    from_files,
                    from_priority,
                    from_files,
                )
            )
        )
        == exists[:3]
    )


def test__parse_location_star() -> None:
    con_loc = parse_location("/a/b/a.*")
    assert tuple(con_loc.get_possible_locations()) == (Path("/a/b/a.yaml"), Path("/a/b/a.yml"))


def test__parse_location_ystar() -> None:
    con_loc = parse_location("/a/b/a.y*")
    assert tuple(con_loc.get_possible_locations()) == (Path("/a/b/a.yaml"), Path("/a/b/a.yml"))


def test__parse_location_yml() -> None:
    con_loc = parse_location("/a/b/a.yml")
    assert tuple(con_loc.get_possible_locations()) == (Path("/a/b/a.yaml"), Path("/a/b/a.yml"))


def test__parse_location_file() -> None:
    con_loc = parse_location("/a/b/a")
    assert tuple(con_loc.get_possible_locations()) == (Path("/a/b/a"),)

    con_loc = parse_location("/a/b/a.yaml")
    assert tuple(con_loc.get_possible_locations()) == (Path("/a/b/a.yaml"),)

    con_loc = parse_location("/a/b/a.doc")
    assert tuple(con_loc.get_possible_locations()) == (Path("/a/b/a.doc"),)


def test__parse_location_home() -> None:
    con_loc = parse_location("~/a")
    assert tuple(con_loc.get_possible_locations()) == (Path("~/a").expanduser().resolve(),)


def test__parse_location_join() -> None:
    con_loc = parse_location(
        Path(__file__).parent / "a",
    )
    assert tuple(con_loc.get_possible_locations()) == (Path(__file__).parent / "a",)


def test__parse_location_type_error() -> None:
    with pytest.raises(TypeError):
        parse_location(None)  # type: ignore
