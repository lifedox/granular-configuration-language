import operator as op
import os
import typing as typ
from functools import cached_property, lru_cache
from itertools import chain, islice
from pathlib import Path

from granular_configuration_language._utils import OrderedSet

PathOrStr = Path | str | os.PathLike


@lru_cache()
def _resolve_path(path: Path) -> Path:
    return path.expanduser().resolve()


def _convert_to_path(path: PathOrStr) -> Path:
    if isinstance(path, Path):
        return path
    else:
        return Path(path)


def path_repr(path: Path) -> str:  # pragma: no cover
    return str(path.relative_to(Path.cwd()))


class BaseLocation(typ.Iterable[Path], typ.Hashable):
    pass


class PrioritizedLocations(BaseLocation):
    __slots__ = ("paths",)

    def __init__(self, paths: tuple[Path, ...]) -> None:
        self.paths: typ.Final = paths

    def __iter__(self) -> typ.Iterator[Path]:
        return islice(filter(op.methodcaller("is_file"), self.paths), 1)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, PrioritizedLocations) and self.paths == value.paths

    def __hash__(self) -> int:
        return self.__hash

    @cached_property
    def __hash(self) -> int:
        return hash(self.paths)

    def __repr__(self) -> str:
        return f"<PrioritizedLocations=[{','.join(map(path_repr, self.paths))}]>"


class Location(BaseLocation):
    __slots__ = "path"

    def __init__(self, path: Path) -> None:
        self.path: typ.Final = path

    def __iter__(self) -> typ.Iterator[Path]:
        if self.path.is_file():
            yield self.path

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Location) and self.path == value.path

    def __hash__(self) -> int:
        return self.__hash

    @cached_property
    def __hash(self) -> int:
        return hash(self.path)

    def __repr__(self) -> str:
        return f"<Location={path_repr(self.path)}>"


SUFFIX_CONFIG: typ.Final[dict[str, typ.Sequence[str]]] = {
    ".*": (".yaml", ".yml"),
    ".y*": (".yaml", ".yml"),
    ".yml": (".yaml", ".yml"),
}


@lru_cache()
def _convert_to_location(path: Path) -> BaseLocation:
    if path.suffix in SUFFIX_CONFIG:
        return PrioritizedLocations(tuple(map(path.with_suffix, SUFFIX_CONFIG[path.suffix])))
    else:
        return Location(path)


class Locations(BaseLocation):
    def __init__(self, locations: typ.Iterable[PathOrStr]) -> None:
        self.locations: typ.Final = tuple(
            map(_convert_to_location, map(_resolve_path, map(_convert_to_path, locations)))
        )

    def __iter__(self) -> typ.Iterator[Path]:
        return iter(OrderedSet(chain.from_iterable(self.locations)))

    def __bool__(self) -> bool:
        return bool(self.locations)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Locations) and self.locations == value.locations

    def __hash__(self) -> int:
        return self.__hash

    @cached_property
    def __hash(self) -> int:
        return sum(map(hash, self.locations))

    def __repr__(self) -> str:
        return f"<Locations=[{','.join(map(repr, self.locations))}]>"
