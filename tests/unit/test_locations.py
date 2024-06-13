import os
import typing as typ
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch

from granular_configuration._locations import (
    ConfigurationFiles,
    ConfigurationLocations,
    ConfigurationMultiNamedFiles,
    _get_files_from_locations,
    get_all_unique_locations,
    parse_location,
)


class TestLocations(unittest.TestCase):
    def test__get_files_from_locations(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(Path, map(dir_func, ["a/b", "a", "b", "c", "d", "c"])))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(Path, list(map(dir_func, ["g/b.txt", "g/h.txt"]))))

        exists = list(map(Path, list(map(dir_func, ["a/b/t2.txt", "g/h.txt", "c/t.txt", "c/t2.txt"]))))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists[:3])

    def test__get_files_from_locations_no_filename(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(Path, map(dir_func, ["a/b", "a", "b", "c", "d", "c"])))
        filenames: typ.List[str] = []
        files = list(map(Path, list(map(dir_func, ["g/b.txt", "g/h.txt"]))))

        exists = list(map(Path, map(dir_func, ["g/h.txt"])))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists)

    def test__get_files_from_locations_no_dirs(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories: typ.List[Path] = []
        filenames = ["t.txt", "t2.txt"]
        files = list(map(Path, list(map(dir_func, ["g/b.txt", "g/h.txt"]))))

        exists = list(map(Path, map(dir_func, ["g/h.txt"])))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists)

    def test__ConfigurationLocations(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = tuple(map(Path, map(dir_func, ["a/b", "a", "b", "c", "d", "c"])))
        filenames = ("t.txt", "t2.txt")
        files = tuple(map(Path, map(dir_func, ["g/b.txt", "g/h.txt"])))

        exists = list(map(Path, map(dir_func, ["g/h.txt", "a/b/t2.txt", "c/t.txt", "c/t2.txt"])))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        with patch(
            "granular_configuration._locations._get_files_from_locations", side_effect=_get_files_from_locations
        ) as loc_mock:
            from_files = ConfigurationLocations(files=files)
            from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

            loc_mock.assert_not_called()

            assert list(from_files.get_locations()) == exists[0:1]
            loc_mock.assert_called_with(filenames=None, directories=None, files=files)

            assert list(from_priority.get_locations()) == exists[1:3]
            loc_mock.assert_called_with(filenames=filenames, directories=directories, files=None)

            assert loc_mock.call_count == 2

    def test__ConfigurationFiles(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(Path, map(dir_func, ["placeholder_test1.yaml", "placeholder_test2.yaml"])))

        assert list(ConfigurationFiles(files).get_locations()) == files

    def test__ConfigurationFiles_from_args(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(Path, map(dir_func, ["placeholder_test1.yaml", "placeholder_test2.yaml"])))

        assert list(ConfigurationFiles.from_args(*files).get_locations()) == files

    def test__ConfigurationMultiNamedFiles(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t2.txt"]

        exists = list(map(Path, map(dir_func, ["a/b/t2.txt", "c/t2.txt"])))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        assert (
            list(ConfigurationMultiNamedFiles(filenames=filenames, directories=directories).get_locations()) == exists
        )

    def test_get_all_unique_locations(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(Path, map(dir_func, ["g/h.txt", "a/b/t2.txt", "c/t.txt", "c/t2.txt"])))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        from_files = ConfigurationLocations(files=files)
        from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

        assert list(get_all_unique_locations([from_files, from_priority, from_files])) == exists[:3]
        assert (
            list(get_all_unique_locations([from_files, from_priority, from_files, from_priority, from_files]))
            == exists[:3]
        )

    def test__parse_location_star(self) -> None:
        con_loc = parse_location("/a/b/a.*")
        assert con_loc.directories is not None
        assert con_loc.filenames is not None
        assert con_loc.files is None
        self.assertSequenceEqual(con_loc.directories, [Path("/a/b")])
        self.assertSequenceEqual(con_loc.filenames, ["a.yaml", "a.yml", "a.ini"])

    def test__parse_location_ini(self) -> None:
        con_loc = parse_location("/a/b/a.ini")
        assert con_loc.directories is not None
        assert con_loc.filenames is not None
        assert con_loc.files is None
        self.assertSequenceEqual(con_loc.directories, [Path("/a/b")])
        self.assertSequenceEqual(con_loc.filenames, ["a.ini", "a.yaml", "a.yml"])

    def test__parse_location_ystar(self) -> None:
        con_loc = parse_location("/a/b/a.y*")
        assert con_loc.directories is not None
        assert con_loc.filenames is not None
        assert con_loc.files is None
        self.assertSequenceEqual(con_loc.directories, [Path("/a/b")])
        self.assertSequenceEqual(con_loc.filenames, ["a.yaml", "a.yml"])

    def test__parse_location_yml(self) -> None:
        con_loc = parse_location("/a/b/a.yml")
        assert con_loc.directories is not None
        assert con_loc.filenames is not None
        assert con_loc.files is None
        self.assertSequenceEqual(con_loc.directories, [Path("/a/b")])
        self.assertSequenceEqual(con_loc.filenames, ["a.yaml", "a.yml"])

    def test__parse_location_file(self) -> None:
        con_loc = parse_location("/a/b/a")
        assert con_loc.directories is None
        assert con_loc.filenames is None
        assert con_loc.files is not None
        self.assertSequenceEqual(con_loc.files, [Path("/a/b/a")])

        con_loc = parse_location("/a/b/a.yaml")
        assert con_loc.directories is None
        assert con_loc.filenames is None
        assert con_loc.files is not None
        self.assertSequenceEqual(con_loc.files, [Path("/a/b/a.yaml")])

        con_loc = parse_location("/a/b/a.doc")
        assert con_loc.directories is None
        assert con_loc.filenames is None
        assert con_loc.files is not None
        self.assertSequenceEqual(con_loc.files, [Path("/a/b/a.doc")])

    def test__parse_location_home(self) -> None:
        con_loc = parse_location("~/a")
        assert con_loc.directories is None
        assert con_loc.filenames is None
        assert con_loc.files is not None
        self.assertSequenceEqual(con_loc.files, [Path("~/a").expanduser().resolve()])

    def test__parse_location_join(self) -> None:
        con_loc = parse_location(os.path.join(__file__, "a"))
        assert con_loc.directories is None
        assert con_loc.filenames is None
        assert con_loc.files is not None
        self.assertSequenceEqual(con_loc.files, [Path(__file__) / "a"])

    def test__parse_location_type_error(self) -> None:
        with self.assertRaises(TypeError):
            parse_location(None)  # type: ignore


if __name__ == "__main__":
    unittest.main()
