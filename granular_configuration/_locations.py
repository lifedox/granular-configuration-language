import abc
import operator as op
import os
import typing as typ
from itertools import chain, islice
from pathlib import Path

from granular_configuration._utils import OrderedSet

PathOrStr = Path | str | os.PathLike


def _absolute_paths(paths: typ.Iterable[Path]) -> typ.Sequence[Path]:
    return tuple(map(op.methodcaller("resolve"), map(op.methodcaller("expanduser"), paths)))


class ConfigurationLocations(abc.ABC):

    @abc.abstractmethod
    def get_locations(self) -> OrderedSet[Path]: ...  # pragma: no cover  # abstractmethod

    @abc.abstractmethod
    def get_possible_locations(self) -> OrderedSet[Path]: ...  # pragma: no cover  # abstractmethod


_CLS = typ.TypeVar("_CLS", bound="ConfigurationFiles")


class ConfigurationFiles(ConfigurationLocations):
    def __init__(self, files: typ.Sequence[PathOrStr]) -> None:
        self.files: typ.Final = _absolute_paths(map(Path, files))

    @classmethod
    def from_args(cls: typ.Type[_CLS], *files: PathOrStr) -> _CLS:
        return cls(files)

    def get_locations(self) -> OrderedSet[Path]:
        return OrderedSet(filter(op.methodcaller("is_file"), self.get_possible_locations()))

    def get_possible_locations(self) -> OrderedSet[Path]:
        return OrderedSet(self.files)


class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames: typ.Sequence[str], directories: typ.Sequence[PathOrStr]) -> None:
        self.filenames: typ.Final = filenames
        self.directories: typ.Final = _absolute_paths(map(Path, directories))


    def get_locations(self) -> OrderedSet[Path]:
        def _get_first_existing_file_from_directory(directory: Path) -> typ.Iterator[Path]:
            return islice(filter(op.methodcaller("is_file"), map(directory.__truediv__, self.filenames)), 1)

        return OrderedSet(chain.from_iterable(map(_get_first_existing_file_from_directory, self.directories)))

    def get_possible_locations(self) -> OrderedSet[Path]:
        def _get_first_existing_file_from_directory(directory: Path) -> typ.Iterator[Path]:
            return map(directory.__truediv__, self.filenames)

        return OrderedSet(chain.from_iterable(map(_get_first_existing_file_from_directory, self.directories)))


def get_all_unique_locations(locations: typ.Iterable[ConfigurationLocations]) -> OrderedSet[Path]:
    return OrderedSet(chain.from_iterable(map(op.methodcaller("get_locations"), locations)))


def _parse_location_path(location: Path) -> ConfigurationLocations:
    dirname = location.parent
    basename = location.stem
    ext = location.suffix
    if ext == ".*":
        return ConfigurationMultiNamedFiles(filenames=(basename + ".yaml", basename + ".yml"), directories=(dirname,))
    elif ext in (".y*", ".yml"):
        return ConfigurationMultiNamedFiles(filenames=(basename + ".yaml", basename + ".yml"), directories=(dirname,))
    else:
        return ConfigurationFiles(files=(location,))


def parse_location(location: PathOrStr | ConfigurationLocations) -> ConfigurationLocations:
    if isinstance(location, ConfigurationLocations):
        return location
    elif isinstance(location, str):
        return _parse_location_path(Path(location))
    elif isinstance(location, Path):
        return _parse_location_path(location)
    else:
        raise TypeError(
            "Expected ConfigurationFiles, ConfigurationMultiNamedFiles, ConfigurationMultiNamedFiles, pathlib.Path\
, or a str. Not ({})".format(
                type(location).__name__
            )
        )
