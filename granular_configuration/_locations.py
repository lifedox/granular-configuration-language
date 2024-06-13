import operator as op
import os
import typing as typ
from itertools import chain, islice
from pathlib import Path

from granular_configuration.utils import OrderedSet

PathOrStr = typ.Union[Path, str, os.PathLike]


def _absolute_paths(paths: typ.Iterable[Path]) -> typ.Sequence[Path]:
    return tuple(map(op.methodcaller("resolve"), map(op.methodcaller("expanduser"), paths)))


def _get_existing_files_from_directories(
    filenames: typ.Sequence[str], directories: typ.Sequence[Path]
) -> OrderedSet[Path]:
    def _get_first_existing_file_from_directory(directory: Path) -> typ.Iterator[Path]:
        return islice(filter(op.methodcaller("is_file"), map(directory.__truediv__, filenames)), 1)

    return OrderedSet(chain.from_iterable(map(_get_first_existing_file_from_directory, directories)))


def _get_existing_files(files: typ.Sequence[Path]) -> OrderedSet[Path]:
    return OrderedSet(filter(op.methodcaller("is_file"), files))


def _get_files_from_locations(
    filenames: typ.Optional[typ.Sequence[str]] = None,
    directories: typ.Optional[typ.Sequence[Path]] = None,
    files: typ.Optional[typ.Sequence[Path]] = None,
) -> OrderedSet[Path]:

    result: OrderedSet[Path] = OrderedSet()

    if filenames and directories:
        result.update(_get_existing_files_from_directories(filenames, directories))

    if files:
        result.update(_get_existing_files(files))

    return result


class ConfigurationLocations(object):
    __filenames: typ.Optional[typ.Sequence[str]]
    __directories: typ.Optional[typ.Sequence[Path]]
    __files: typ.Optional[typ.Sequence[Path]]

    def __init__(
        self,
        filenames: typ.Optional[typ.Sequence[str]] = None,
        directories: typ.Optional[typ.Sequence[PathOrStr]] = None,
        files: typ.Optional[typ.Sequence[PathOrStr]] = None,
    ) -> None:
        if files and (filenames or directories):
            raise ValueError("files cannot be defined with filenames and directories.")
        elif bool(filenames) ^ bool(directories):
            raise ValueError("filenames and directories are a required pair.")

        self.__filenames = filenames
        self.__directories = _absolute_paths(map(Path, directories)) if directories else None
        self.__files = _absolute_paths(map(Path, files)) if files else None

    def get_locations(self) -> OrderedSet[Path]:
        return _get_files_from_locations(filenames=self.__filenames, directories=self.__directories, files=self.__files)

    @property
    def filenames(self) -> typ.Optional[typ.Sequence[str]]:
        return self.__filenames

    @property
    def directories(self) -> typ.Optional[typ.Sequence[Path]]:
        return self.__directories

    @property
    def files(self) -> typ.Optional[typ.Sequence[Path]]:
        return self.__files


_CLS = typ.TypeVar("_CLS", bound="ConfigurationFiles")


class ConfigurationFiles(ConfigurationLocations):
    def __init__(self, files: typ.Sequence[PathOrStr]) -> None:
        super(ConfigurationFiles, self).__init__(filenames=None, directories=None, files=files)

    @classmethod
    def from_args(cls: typ.Type[_CLS], *files: PathOrStr) -> _CLS:
        return cls(files)


class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames: typ.Sequence[str], directories: typ.Sequence[PathOrStr]) -> None:
        super(ConfigurationMultiNamedFiles, self).__init__(filenames=filenames, directories=directories, files=None)


def get_all_unique_locations(locations: typ.Iterable[ConfigurationLocations]) -> OrderedSet[Path]:
    return OrderedSet(chain.from_iterable(map(op.methodcaller("get_locations"), locations)))


def _parse_location_path(location: Path) -> ConfigurationLocations:
    dirname = location.parent
    basename = location.stem
    ext = location.suffix
    if ext == ".*":
        return ConfigurationMultiNamedFiles(
            filenames=(basename + ".yaml", basename + ".yml", basename + ".ini"), directories=(dirname,)
        )
    elif ext in (".y*", ".yml"):
        return ConfigurationMultiNamedFiles(filenames=(basename + ".yaml", basename + ".yml"), directories=(dirname,))
    elif ext == ".ini":
        return ConfigurationMultiNamedFiles(
            filenames=(basename + ".ini", basename + ".yaml", basename + ".yml"), directories=(dirname,)
        )
    else:
        return ConfigurationFiles(files=(location,))


def parse_location(location: typ.Union[PathOrStr, ConfigurationLocations]) -> ConfigurationLocations:
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
