from __future__ import annotations

import collections.abc as tabc
import os
import sys
import typing as typ
from collections import OrderedDict, deque
from functools import partial

from granular_configuration_language.exceptions import EnvironmentVaribleNotFound

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: typ.Callable) -> typ.Callable:
        return func


consume = typ.cast(tabc.Callable[[tabc.Iterable], None], partial(deque, maxlen=0))

_T = typ.TypeVar("_T")


class OrderedSet(tabc.MutableSet[_T], tabc.Reversible[_T], typ.Generic[_T]):
    def __init__(self, iterable: tabc.Iterable[_T] | None = None) -> None:
        self.__backend: OrderedDict[_T, None] = OrderedDict()
        if iterable is not None:
            consume(map(self.add, iterable))

    @override
    def __contains__(self, item: typ.Any) -> bool:
        return item in self.__backend

    @override
    def __iter__(self) -> tabc.Iterator[_T]:
        return iter(self.__backend)

    @override
    def __len__(self) -> int:
        return len(self.__backend)

    @override
    def add(self, value: _T) -> None:
        self.__backend[value] = None

    @override
    def discard(self, value: _T) -> None:
        del self.__backend[value]

    @override
    def __reversed__(self) -> tabc.Iterator[_T]:
        return reversed(self.__backend)


def get_environment_variable(name: str, default: str | tabc.Callable[[], str] | None = None) -> str:
    name = name.replace("::", ":")
    if name in os.environ:
        return os.environ[name]
    elif default is None:
        raise EnvironmentVaribleNotFound(name)
    elif callable(default):
        return default()
    else:
        return default
