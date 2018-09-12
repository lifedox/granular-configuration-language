import typing as typ

from functools import partial
from contextlib import contextmanager

from granular_configuration._load import load_file
from granular_configuration.utils import OrderedSet


class Patch(typ.Mapping):
    def __init__(self, patch_map: typ.Mapping, parent: typ.Optional["Patch"] = None, allow_new_keys: bool = False) -> None: ...

    def __getitem__(self, name: typ.Any) -> typ.Any: ...

    def __iter__(self) -> typ.Iterator: ...

    def __len__(self) -> int: ...

    def __hash__(self) -> int: ...

    def __eq__(self, rhs: typ.Any) -> bool: ...

    @property
    def alive(self) -> bool: ...

    def kill(self) -> None: ...

    @property
    def allows_new_keys(self) -> bool: ...

    def make_child(self, name: str, for_patch: bool) -> "Patch": ...


class Configuration(typ.Dict):
    def __getattr__(self, name: str) -> typ.Any: ...

    def exists(self, key: typ.Any) -> bool: ...

    def as_dict(self) -> typ.Dict: ...

    def _raw_items(self) -> typ.Iterator[typ.Tuple[typ.Any, typ.Any]]: ...

    @contextmanager
    def patch(self, patch_map: typ.Mapping, allow_new_keys: bool = False) -> typ.Generator[None, None, None]: ...




_load_file = partial(load_file, obj_pairs_hook=Configuration)


def _build_configuration(locations: str) -> Configuration: ...


def _get_files_from_locations(filenames: typ.Optional[typ.Sequence[str]] = None, directories: typ.Optional[typ.Sequence[str]] = None, files: typ.Optional[typ.Sequence[str]] = None) -> OrderedSet[str]: ...


class ConfigurationLocations(object):
    filenames: typ.Optional[typ.Sequence[str]]
    directories: typ.Optional[typ.Sequence[str]]
    files: typ.Optional[typ.Sequence[str]]

    def __init__(self, filenames: typ.Optional[typ.Sequence[str]] = None, directories: typ.Optional[typ.Sequence[str]] = None, files: typ.Optional[typ.Sequence[str]] = None) -> None: ...

    def get_locations(self) -> OrderedSet[str]: ...


_CLS = typ.TypeVar('_CLS', bound='ConfigurationFiles')

class ConfigurationFiles(ConfigurationLocations):
    def __init__(self, files: typ.Sequence[str]) -> None:
        super(ConfigurationFiles, self).__init__(filenames=None, directories=None, files=files)

    @classmethod
    def from_args(cls: typ.Type[_CLS], *files: str) -> _CLS: ...


class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames: typ.Sequence[str], directories: typ.Sequence[str]) -> None: ...


def _get_all_unique_locations(locations: typ.Iterable[str]) -> OrderedSet[str]: ...


def _parse_location(location: typ.Union[str, ConfigurationLocations]) -> ConfigurationLocations: ...


class LazyLoadConfiguration(Configuration):
    """
    Provides a lazy interface for loading Configuration from ConfigurationLocations definitions on first access.
    """
    def __init__(self, *load_order_location: typ.Union[str, ConfigurationLocations], base_path: typ.Optional[typ.Union[str, typ.Sequence[str]]]) -> None: ...

    def load_configure(self) -> None: ...

    @property
    def config(self) -> Configuration: ...
