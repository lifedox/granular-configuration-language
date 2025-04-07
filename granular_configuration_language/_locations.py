from __future__ import annotations

import collections.abc as tabc
import operator as op
import os
import sys
import typing as typ
from functools import cached_property, lru_cache
from itertools import chain, islice
from pathlib import Path

from granular_configuration_language._utils import OrderedSet

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func


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


class BaseLocation(tabc.Iterable[Path], typ.Hashable):
    pass


class PrioritizedLocations(BaseLocation):
    __slots__ = ("paths",)

    def __init__(self, paths: tuple[Path, ...]) -> None:
        self.paths: typ.Final = paths

    @override
    def __iter__(self) -> tabc.Iterator[Path]:
        return islice(filter(op.methodcaller("is_file"), self.paths), 1)

    @override
    def __eq__(self, value: object) -> bool:
        return isinstance(value, PrioritizedLocations) and self.paths == value.paths

    @override
    def __hash__(self) -> int:
        return self.__hash

    @cached_property
    def __hash(self) -> int:
        return hash(self.paths)

    @override
    def __repr__(self) -> str:
        return f"<PrioritizedLocations=[{','.join(map(path_repr, self.paths))}]>"


class Location(BaseLocation):
    __slots__ = "path"

    def __init__(self, path: Path) -> None:
        self.path: typ.Final = path

    @override
    def __iter__(self) -> tabc.Iterator[Path]:
        if self.path.is_file():
            yield self.path

    @override
    def __eq__(self, value: object) -> bool:
        return isinstance(value, Location) and self.path == value.path

    @override
    def __hash__(self) -> int:
        return self.__hash

    @cached_property
    def __hash(self) -> int:
        return hash(self.path)

    @override
    def __repr__(self) -> str:
        return f"<Location={path_repr(self.path)}>"


SUFFIX_CONFIG: typ.Final[dict[str, tabc.Sequence[str]]] = {
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
    def __init__(self, locations: tabc.Iterable[PathOrStr]) -> None:
        self.locations: typ.Final = tuple(
            map(_convert_to_location, map(_resolve_path, map(_convert_to_path, locations)))
        )

    @override
    def __iter__(self) -> tabc.Iterator[Path]:
        return iter(OrderedSet(chain.from_iterable(self.locations)))

    def __bool__(self) -> bool:
        return bool(self.locations)

    @override
    def __eq__(self, value: object) -> bool:
        return isinstance(value, Locations) and self.locations == value.locations

    @override
    def __hash__(self) -> int:
        return self.__hash

    @cached_property
    def __hash(self) -> int:
        return sum(map(hash, self.locations))

    @override
    def __repr__(self) -> str:
        return f"<Locations=[{','.join(map(repr, self.locations))}]>"
