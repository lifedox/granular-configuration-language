import typing as typ

_RT = typ.TypeVar("_RT")

class Placeholder:
    __slot__ = ("message",)

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class LazyRoot:
    def __init__(self) -> None:
        self.root: typ.Any = None


class LazyEval(typ.Generic[_RT]):
    __slots__ = ("value",)

    def __init__(self, value: typ.Callable[[], _RT]) -> None:
        assert callable(value)
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


LazyEvalStr = LazyEval[str]
LazyEvalRootStateStr = LazyEvalRootState[str]