import unittest
from mock import patch
import os
from functools import partial


from granular_configuration._config import (
    _get_files_from_locations,
    _get_all_unique_locations,
    _parse_location,
    ConfigurationLocations,
    ConfigurationFiles,
    ConfigurationMultiNamedFiles,
)


class TestLocations(unittest.TestCase):
    def test__get_files_from_locations(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["a/b/t2.txt", "g/h.txt", "c/t.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists[:3])

    def test__get_files_from_locations_no_filename(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = []
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists)

    def test__get_files_from_locations_no_dirs(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = []
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists)

    def test__ConfigurationLocations(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt", "a/b/t2.txt", "c/t.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        with patch(
            "granular_configuration._config._get_files_from_locations", side_effect=_get_files_from_locations
        ) as loc_mock:
            from_files = ConfigurationLocations(files=files)
            from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

            loc_mock.assert_not_called()

            assert list(from_files.get_locations()) == exists[0:1]
            loc_mock.assert_called_with(filenames=None, directories=None, files=files)

            assert list(from_priority.get_locations()) == exists[1:3]
            loc_mock.assert_called_with(filenames=filenames, directories=directories, files=None)

            assert loc_mock.call_count == 2

    def test__ConfigurationFiles(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(dir_func, ["placeholder_test1.yaml", "placeholder_test2.yaml"]))

        assert list(ConfigurationFiles(files).get_locations()) == files

    def test__ConfigurationFiles_from_args(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(dir_func, ["placeholder_test1.yaml", "placeholder_test2.yaml"]))

        assert list(ConfigurationFiles.from_args(*files).get_locations()) == files

    def test__ConfigurationMultiNamedFiles(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t2.txt"]

        exists = list(map(dir_func, ["a/b/t2.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        assert (
            list(ConfigurationMultiNamedFiles(filenames=filenames, directories=directories).get_locations()) == exists
        )

    def test__get_all_unique_locations(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt", "a/b/t2.txt", "c/t.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        from_files = ConfigurationLocations(files=files)
        from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

        assert list(_get_all_unique_locations([from_files, from_priority, from_files])) == exists[:3]
        assert (
            list(_get_all_unique_locations([from_files, from_priority, from_files, from_priority, from_files]))
            == exists[:3]
        )

    def test__parse_location_star(self):
        con_loc = _parse_location("/a/b/a.*")
        self.assertSequenceEqual(con_loc.directories, ["/a/b"])
        self.assertSequenceEqual(con_loc.filenames, ["a.yaml", "a.yml", "a.ini"])
        self.assertIsNone(con_loc.files)

        con_loc = _parse_location("/a/b/a.ini")
        self.assertSequenceEqual(con_loc.directories, ["/a/b"])
        self.assertSequenceEqual(con_loc.filenames, ["a.yaml", "a.yml", "a.ini"])
        self.assertIsNone(con_loc.files)

    def test__parse_location_ystar(self):
        con_loc = _parse_location("/a/b/a.y*")
        self.assertSequenceEqual(con_loc.directories, ["/a/b"])
        self.assertSequenceEqual(con_loc.filenames, ["a.yaml", "a.yml"])
        self.assertIsNone(con_loc.files)

        con_loc = _parse_location("/a/b/a.yml")
        self.assertSequenceEqual(con_loc.directories, ["/a/b"])
        self.assertSequenceEqual(con_loc.filenames, ["a.yaml", "a.yml"])
        self.assertIsNone(con_loc.files)

    def test__parse_location_file(self):
        con_loc = _parse_location("/a/b/a")
        self.assertIsNone(con_loc.directories)
        self.assertIsNone(con_loc.filenames)
        self.assertSequenceEqual(con_loc.files, ["/a/b/a"])

        con_loc = _parse_location("/a/b/a.yaml")
        self.assertIsNone(con_loc.directories)
        self.assertIsNone(con_loc.filenames)
        self.assertSequenceEqual(con_loc.files, ["/a/b/a.yaml"])

        con_loc = _parse_location("/a/b/a.doc")
        self.assertIsNone(con_loc.directories)
        self.assertIsNone(con_loc.filenames)
        self.assertSequenceEqual(con_loc.files, ["/a/b/a.doc"])

    def test__parse_location_home(self):
        con_loc = _parse_location("~/a")
        self.assertIsNone(con_loc.directories)
        self.assertIsNone(con_loc.filenames)
        self.assertSequenceEqual(con_loc.files, [os.path.abspath(os.path.expanduser("~/a"))])

    def test__parse_location_join(self):
        con_loc = _parse_location(os.path.join(__file__, "a"))
        self.assertIsNone(con_loc.directories)
        self.assertIsNone(con_loc.filenames)
        self.assertSequenceEqual(con_loc.files, [os.path.join(__file__, "a")])

    def test__parse_location_type_error(self):
        with self.assertRaises(TypeError):
            _parse_location(None)


if __name__ == "__main__":
    unittest.main()
