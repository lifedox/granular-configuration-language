import abc
import typing as typ
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from threading import RLock

_RT = typ.TypeVar("_RT")

RootType = typ.NewType("RootType", typ.Mapping)
Root = RootType | None
Tag = typ.NewType("Tag", str)


class Masked(str):
    def __repr__(self) -> str:
        return "'<****>'"


class Placeholder:
    __slot__ = ("message",)

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class LazyRoot:
    __slots__ = "__root"

    def __init__(self) -> None:
        self.__root: Root = None

    def _set_root(self, root: typ.Any) -> None:
        self.__root = root

    @property
    def root(self) -> Root:
        return self.__root

    @staticmethod
    def with_root(root: typ.Mapping | Root) -> "LazyRoot":
        lazy_root = LazyRoot()
        lazy_root._set_root(root)
        return lazy_root


class LazyEval(abc.ABC, typ.Generic[_RT]):
    def __init__(self, tag: Tag) -> None:
        self.tag = tag
        self.done = False
        self.lock = RLock()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.tag}>"

    def run(self) -> _RT:
        if self.done:  # pragma: no cover
            return self.__result
        else:
            with self.lock:
                result = self.__result
                self.done = True

            del self.lock
            return result

    @cached_property
    def result(self) -> typ.Any:
        """
        Result of LazyEval, completing any chains
        """
        result = self.run()
        while isinstance(result, LazyEval):
            result = result.run()
        return result

    @cached_property
    def __result(self) -> _RT:
        return self._run()

    @abc.abstractmethod
    def _run(self) -> _RT: ...  # pragma: no cover


@dataclass(frozen=True, kw_only=True)
class LoadOptions:
    obj_pairs_func: typ.Type[typ.Mapping]
    mutable: bool
    file_location: Path | None
    relative_to_directory: Path


@dataclass(frozen=True, kw_only=True)
class StateHolder:
    options: LoadOptions
    lazy_root_obj: LazyRoot
