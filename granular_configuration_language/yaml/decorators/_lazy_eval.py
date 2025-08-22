from __future__ import annotations

import collections.abc as tabc
import sys
import typing as typ

from granular_configuration_language.exceptions import ErrorWhileLoadingConfig
from granular_configuration_language.yaml.classes import RT, LazyEval, LazyRoot, Root, Tag

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func


def pickling_error_occur(*arg: typ.Any) -> typ.NoReturn:  # pragma: no cover
    raise ErrorWhileLoadingConfig(
        "An error occurred due to unexpected state left by unpickling. Please report this with replication steps."
    )


class LazyEvalBasic(LazyEval[RT]):
    def __init__(self, tag: Tag, value: tabc.Callable[[], RT]) -> None:
        super().__init__(tag)
        self.__value = value

    @override
    def _run(self) -> RT:
        return self.__value()

    @override
    def __getstate__(self) -> typ.Any:
        self.result  # noqa: B018  # Run to get rid of the RLock and before ruining this instance with pickling_error_occur
        self.__value = pickling_error_occur
        return super().__getstate__()


class LazyEvalWithRoot(LazyEval[RT]):
    def __init__(self, tag: Tag, root: LazyRoot, value: tabc.Callable[[Root], RT]) -> None:
        super().__init__(tag)
        self.__value = value
        self.__lazy_root = root

    @override
    def _run(self) -> RT:
        return self.__value(self.__lazy_root.root)

    @override
    def __getstate__(self) -> typ.Any:
        self.result  # noqa: B018  # Run to get rid of the RLock and before ruining this instance with pickling_error_occur
        self.__value = pickling_error_occur
        return super().__getstate__()
