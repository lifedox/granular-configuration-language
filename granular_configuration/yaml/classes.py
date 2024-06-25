import typing as typ
from dataclasses import dataclass
from functools import cache
from pathlib import Path

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


class LazyEval(typ.Generic[_RT]):
    __slots__ = ("value", "tag")

    def __init__(self, tag: Tag, value: typ.Callable[[], _RT]) -> None:
        self.tag = tag
        self.value: typ.Callable[..., _RT] = value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.tag}>"

    @cache
    def run(self) -> _RT:
        return self._run()

    def _run(self) -> _RT:
        return self.value()


class LazyEvalRootState(LazyEval[_RT]):
    __slots__ = ("root",)

    def __init__(self, tag: Tag, root: LazyRoot, value: typ.Callable[[typ.Any], _RT]) -> None:
        self.tag = tag
        self.value: typ.Callable[..., _RT] = value
        self.root = root

    def _run(self) -> _RT:
        return self.value(self.root.root)


_OPH = typ.Optional[typ.Type[typ.MutableMapping]]


@dataclass(frozen=True, kw_only=True)
class StateOptions:
    obj_pairs_func: _OPH
    file_relative_path: Path


@dataclass(frozen=True, kw_only=True)
class StateHolder:
    options: StateOptions
    lazy_root_obj: LazyRoot
