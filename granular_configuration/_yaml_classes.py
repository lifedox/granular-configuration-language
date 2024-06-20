import typing as typ
from dataclasses import dataclass
from pathlib import Path

_RT = typ.TypeVar("_RT")

RootType = typ.NewType("RootType", object)
Root = RootType | None


class Placeholder:
    __slot__ = ("message",)

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class LazyRoot:
    def __init__(self) -> None:
        self.root: Root = None

    def _set_root(self, root: typ.Any) -> None:
        self.root = root


class LazyEval(typ.Generic[_RT]):
    __slots__ = ("value",)

    def __init__(self, value: typ.Callable[[], _RT]) -> None:
        self.value: typ.Callable[..., _RT] = value

    def run(self) -> _RT:
        return self.value()


class LazyEvalRootState(LazyEval[_RT]):
    __slots__ = ("root",)

    def __init__(self, root: LazyRoot, value: typ.Callable[[typ.Any], _RT]) -> None:
        self.value: typ.Callable[..., _RT] = value
        self.root = root

    def run(self) -> _RT:
        return self.value(self.root.root)


_OPH = typ.Optional[typ.Type[typ.MutableMapping]]


@dataclass(frozen=True, kw_only=True)
class StateHolder:
    lazy_root_obj: LazyRoot
    obj_pairs_func: _OPH
    file_relative_path: Path
