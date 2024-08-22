import operator as op
import os
import typing as typ
from itertools import chain, islice
from pathlib import Path

from granular_configuration._utils import OrderedSet

PathOrStr = Path | str | os.PathLike


class BaseLocation(typ.Iterable[Path]):
    pass


class PrioritizedLocations(BaseLocation):
    __slots__ = ("paths",)

    def __init__(self, paths: typ.Sequence[Path]) -> None:
        self.paths: typ.Final = paths

    def __iter__(self) -> typ.Iterator[Path]:
        return islice(filter(op.methodcaller("is_file"), self.paths), 1)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, PrioritizedLocations) and self.paths == value.paths

    def __repr__(self) -> str:
        return f"<PrioritizedLocations=[{','.join(map(repr, self.paths))}]>"


class Location(BaseLocation):
    __slots__ = "path"

    def __init__(self, path: Path) -> None:
        self.path: typ.Final = path

    def __iter__(self) -> typ.Iterator[Path]:
        if self.path.is_file():
            yield self.path

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Location) and self.path == value.path

    def __repr__(self) -> str:
        return f"<Location={repr(self.path)}>"


SUFFIX_CONFIG: typ.Final[dict[str, typ.Sequence[str]]] = {
    ".*": (".yaml", ".yml"),
    ".y*": (".yaml", ".yml"),
    ".yml": (".yaml", ".yml"),
}


class Locations(BaseLocation):

    def __init__(self, locations: typ.Iterable[PathOrStr]) -> None:
        self.locations: typ.Final = tuple(
            map(self.__convert_to_base_location, map(self.__expand_path, map(self.__convert_to_path, locations)))
        )

    @staticmethod
    def __convert_to_path(path: PathOrStr) -> Path:
        if isinstance(path, Path):
            return path
        else:
            return Path(path)

    @staticmethod
    def __expand_path(path: Path) -> Path:
        return path.expanduser().resolve()

    @staticmethod
    def __convert_to_base_location(path: Path) -> BaseLocation:
        if path.suffix in SUFFIX_CONFIG:
            return PrioritizedLocations(tuple(map(path.with_suffix, SUFFIX_CONFIG[path.suffix])))
        else:
            return Location(path)

    def __iter__(self) -> typ.Iterator[Path]:
        return iter(OrderedSet(chain.from_iterable(self.locations)))

    def __bool__(self) -> bool:
        return bool(self.locations)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Locations) and self.locations == value.locations

    def __repr__(self) -> str:
        return f"<Locations=[{','.join(map(repr, self.locations))}]>"
