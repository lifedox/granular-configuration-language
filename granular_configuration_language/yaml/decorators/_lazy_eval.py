from __future__ import annotations

import collections.abc as tabc
import sys
import typing as typ

from granular_configuration_language.yaml.classes import RT, LazyEval, LazyRoot, Root, Tag

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func


class LazyEvalBasic(LazyEval[RT]):
    def __init__(self, tag: Tag, value: tabc.Callable[[], RT]) -> None:
        super().__init__(tag)
        self.__value = value

    @override
    def _run(self) -> RT:
        return self.__value()


class LazyEvalWithRoot(LazyEval[RT]):
    def __init__(self, tag: Tag, root: LazyRoot, value: tabc.Callable[[Root], RT]) -> None:
        super().__init__(tag)
        self.__value = value
        self.__lazy_root = root

    @override
    def _run(self) -> RT:
        return self.__value(self.__lazy_root.root)
