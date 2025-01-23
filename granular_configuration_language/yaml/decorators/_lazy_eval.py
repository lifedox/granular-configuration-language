import typing as typ

from granular_configuration_language.yaml.classes import RT, LazyEval, LazyRoot, Root, Tag


class LazyEvalBasic(LazyEval[RT]):
    def __init__(self, tag: Tag, value: typ.Callable[[], RT]) -> None:
        super().__init__(tag)
        self.value: typ.Callable[..., RT] = value

    def _run(self) -> RT:
        return self.value()


class LazyEvalWithRoot(LazyEval[RT]):
    def __init__(self, tag: Tag, root: LazyRoot, value: typ.Callable[[Root], RT]) -> None:
        super().__init__(tag)
        self.value: typ.Callable[..., RT] = value
        self.root = root

    def _run(self) -> RT:
        return self.value(self.root.root)
