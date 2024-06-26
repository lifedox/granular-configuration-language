import typing as typ

from granular_configuration.yaml.classes import _RT, LazyEval, LazyRoot, Root, Tag


class LazyEvalBasic(LazyEval[_RT]):
    def __init__(self, tag: Tag, value: typ.Callable[[], _RT]) -> None:
        super().__init__(tag)
        self.value: typ.Callable[..., _RT] = value

    def _run(self) -> _RT:
        return self.value()


class LazyEvalWithRoot(LazyEval[_RT]):
    def __init__(self, tag: Tag, root: LazyRoot, value: typ.Callable[[Root], _RT]) -> None:
        super().__init__(tag)
        self.value: typ.Callable[..., _RT] = value
        self.root = root

    def _run(self) -> _RT:
        return self.value(self.root.root)
