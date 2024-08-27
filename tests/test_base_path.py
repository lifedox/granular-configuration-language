from granular_configuration.base_path import read_base_path


def test_string_base_path() -> None:
    assert read_base_path("base") == ("base",)


def test_list_base_path() -> None:
    assert read_base_path(["base", "path"]) == ("base", "path")  # type: ignore


def test_no_base_path() -> None:
    assert read_base_path(None) == tuple()
