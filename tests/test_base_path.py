from granular_configuration_language._base_path import read_base_path


def test_string_singular() -> None:
    assert read_base_path("base") == ("base",)


def test_delimited_singular() -> None:
    assert read_base_path("/base") == ("base",)


def test_delimited_singular_ends_slash() -> None:
    assert read_base_path("/base/") == ("base",)


def test_delimited_multiple() -> None:
    assert read_base_path("/base/path") == ("base", "path")  # type: ignore


def test_sequence() -> None:
    assert read_base_path(["base", "path"]) == ("base", "path")  # type: ignore


def test_none() -> None:
    assert read_base_path(None) == tuple()
