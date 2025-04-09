from __future__ import annotations

import collections.abc as tabc
import typing as typ
from concurrent.futures import ThreadPoolExecutor

from granular_configuration_language.yaml.classes import RT, P


class SimpleFuture(typ.Generic[P, RT]):
    __slots__ = ("_executor", "_future", "_func", "__weakref__")

    def __init__(self, func: tabc.Callable[P, RT], /, *args: P.args, **kwargs: P.kwargs) -> None:
        self._executor = ThreadPoolExecutor(1)
        self._future = self._executor.submit(func, *args, **kwargs)
        self._func = func

    @property
    def result(self) -> RT:
        try:
            return self._future.result()
        finally:
            self._executor.shutdown()

    def __del__(self) -> None:
        self._future.cancel()
        self._executor.shutdown(True, cancel_futures=True)

    def __repr__(self) -> str:
        return f"SimpleFuture({self._func})"
