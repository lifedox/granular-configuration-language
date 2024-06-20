import operator as op
import typing as typ
from pathlib import Path
from unittest.mock import patch

import pytest

from granular_configuration._locations import (
    ConfigurationFiles,
    ConfigurationLocations,
    ConfigurationMultiNamedFiles,
    _get_files_from_locations,
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

    locations = _get_files_from_locations(filenames, directories, files)

    assert sorted(locations) == sorted(exists[:3])


def test__get_files_from_locations_no_filename() -> None:
    directories = DIRECTORIES
    filenames: typ.Tuple[str, ...] = tuple()
    files = FILES

    exists = (ASSET_DIR / "g/h.yaml",)

    locations = _get_files_from_locations(filenames, directories, files)

    assert sorted(locations) == sorted(exists)


def test__get_files_from_locations_no_dirs() -> None:
    directories: typ.Tuple[Path, ...] = tuple()
    filenames = FILENAMES
    files = FILES

    exists = (ASSET_DIR / "g/h.yaml",)

    locations = _get_files_from_locations(filenames, directories, files)

    assert sorted(locations) == sorted(exists)


def test__ConfigurationLocations() -> None:
    directories = DIRECTORIES
    filenames = FILENAMES
    files = FILES

    exists = EXISTS

    with patch(
        "granular_configuration._locations._get_files_from_locations", side_effect=_get_files_from_locations
    ) as loc_mock:
        from_files = ConfigurationLocations(files=files)
        from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

        loc_mock.assert_not_called()

        assert tuple(from_files.get_locations()) == exists[0:1]
        loc_mock.assert_called_with(filenames=None, directories=None, files=files)

        assert tuple(from_priority.get_locations()) == exists[1:3]
        loc_mock.assert_called_with(filenames=filenames, directories=directories, files=None)

        assert loc_mock.call_count == 2


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

    from_files = ConfigurationLocations(files=files)
    from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

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
    assert con_loc.directories == (Path("/a/b"),)
    assert con_loc.filenames == (
        "a.yaml",
        "a.yml",
        "a.ini",
    )
    assert con_loc.files is None


def test__parse_location_ini() -> None:
    con_loc = parse_location("/a/b/a.ini")
    assert con_loc.directories == (Path("/a/b"),)
    assert con_loc.filenames == (
        "a.ini",
        "a.yaml",
        "a.yml",
    )
    assert con_loc.files is None


def test__parse_location_ystar() -> None:
    con_loc = parse_location("/a/b/a.y*")
    assert con_loc.directories == (Path("/a/b"),)
    assert con_loc.filenames == (
        "a.yaml",
        "a.yml",
    )
    assert con_loc.files is None


def test__parse_location_yml() -> None:
    con_loc = parse_location("/a/b/a.yml")
    assert con_loc.directories == (Path("/a/b"),)
    assert con_loc.filenames == (
        "a.yaml",
        "a.yml",
    )
    assert con_loc.files is None


def test__parse_location_file() -> None:
    con_loc = parse_location("/a/b/a")
    assert con_loc.directories is None
    assert con_loc.filenames is None
    assert con_loc.files == (Path("/a/b/a"),)

    con_loc = parse_location("/a/b/a.yaml")
    assert con_loc.directories is None
    assert con_loc.filenames is None
    assert con_loc.files == (Path("/a/b/a.yaml"),)

    con_loc = parse_location("/a/b/a.doc")
    assert con_loc.directories is None
    assert con_loc.filenames is None
    assert con_loc.files == (Path("/a/b/a.doc"),)


def test__parse_location_home() -> None:
    con_loc = parse_location("~/a")
    assert con_loc.directories is None
    assert con_loc.filenames is None
    assert con_loc.files == (Path("~/a").expanduser().resolve(),)


def test__parse_location_join() -> None:
    con_loc = parse_location(
        Path(__file__).parent / "a",
    )
    assert con_loc.directories is None
    assert con_loc.filenames is None
    assert con_loc.files == (Path(__file__).parent / "a",)


def test__parse_location_type_error() -> None:
    with pytest.raises(TypeError):
        parse_location(None)  # type: ignore
