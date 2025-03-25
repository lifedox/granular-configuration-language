from __future__ import annotations

import collections.abc as tabc
import os
import sys
import typing as typ
from functools import partial
from itertools import chain
from pathlib import Path

from granular_configuration_language.exceptions import ParsingTriedToCreateALoop
from granular_configuration_language.yaml.classes import LoadOptions, Tag

if sys.version_info >= (3, 12):

    def walkup(file: Path, relative_to: Path) -> Path:
        return file.relative_to(relative_to, walk_up=True)

else:
    import os

    def _get_segments(path: os.PathLike) -> tabc.Iterator[str]:
        head, tail = os.path.split(path)
        if tail:
            yield from _get_segments(head)
            yield tail
        else:
            yield head

    def get_segments(path: os.PathLike) -> list[str]:
        return list(_get_segments(path))

    def walkup(file: Path, relative_to: Path) -> Path:
        # Modified from the 3.12 pathlib.PurePath.relative_to implementation

        for step, path in enumerate([relative_to] + list(relative_to.parents)):
            if file.is_relative_to(path):
                break
            elif path.name == "..":  # pragma: no cover
                raise ValueError(f"'..' segment in {str(relative_to)!r} cannot be walked")
        else:
            raise ValueError(f"{str(file)!r} and {str(relative_to)!r} have different anchors")
        parts = [".."] * step + get_segments(file)[len(get_segments(path)) :]
        return Path(*parts)


ENV_VAR_FILE_EXTENSION: typ.Final = ".environment_variable-a5b55071-b86e-4f22-90fc-c9db335691f6"


def _pretty_source(source: Path, *, relative_to: Path, seen: set[str]) -> str:
    if source.suffix == ENV_VAR_FILE_EXTENSION:
        return "$" + source.stem
    elif source.name not in seen:
        seen.add(source.name)
        return source.name
    else:
        try:
            return str(walkup(source, relative_to))
        except ValueError:
            return "?/" + source.name


def _get_reversed_source_chain(options: LoadOptions) -> tabc.Iterator[Path]:
    if options.previous:
        yield from _get_reversed_source_chain(options.previous)

    if options.file_location:
        yield options.file_location


def stringify_source_chain(sources: tabc.Iterable[Path]) -> str:
    return "→".join(chain(map(partial(_pretty_source, relative_to=Path().resolve(), seen=set()), sources), ("...",)))


def is_in_chain(file: Path, options: LoadOptions) -> bool:
    # Note *.environment_variable don't exist, so `.resolve()` and `.samefile()` fail

    if (
        options.file_location
        and (file.name == options.file_location.name)
        and (file == options.file_location or file.samefile(options.file_location))
    ):
        return True
    elif options.previous:
        return is_in_chain(file, options.previous)
    else:
        return False


def make_chain_message(tag: Tag, value: str, options: LoadOptions) -> ParsingTriedToCreateALoop:
    return ParsingTriedToCreateALoop(
        f"`{tag} {value}` tried to load itself in chain: ({stringify_source_chain(_get_reversed_source_chain(options))})"
    )


def as_file_path(tag: Tag, file_name: str, options: LoadOptions) -> Path:
    """
    .. versionadded:: 2.3.0

    Converts the relative file name to a :py:class:`~pathlib.Path` and checks if it has already been loaded.


    :param Tag tag: Tag doing this, used for error reporting.
    :param str file_name: Name of the file being loaded
    :param LoadOptions options: options from the Tag doing this action, used for tracking chains.
    :return: Path instance
    :rtype: ~pathlib.Path
    """

    result = options.relative_to_directory / file_name

    if is_in_chain(result, options):
        raise make_chain_message(tag, file_name, options)

    return result
