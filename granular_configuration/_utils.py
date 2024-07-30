from __future__ import annotations

import typing as typ
from collections import OrderedDict, deque
from functools import partial

consume = typ.cast(typ.Callable[[typ.Iterable], None], partial(deque, maxlen=0))

_T = typ.TypeVar("_T")


class OrderedSet(typ.MutableSet[_T], typ.Reversible[_T], typ.Generic[_T]):  # pragma: no cover
    def __init__(self, iterable: typ.Optional[typ.Iterable[_T]] = None) -> None:
        self.__backend: OrderedDict[_T, None] = OrderedDict()
        if iterable is not None:
            consume(map(self.add, iterable))

    def __contains__(self, item: typ.Any) -> bool:
        return item in self.__backend

    def __iter__(self) -> typ.Iterator[_T]:
        return iter(self.__backend)

    def __len__(self) -> int:
        return len(self.__backend)

    def add(self, value: _T) -> None:
        self.__backend[value] = None

    def discard(self, value: _T) -> None:
        del self.__backend[value]

    def __reversed__(self) -> typ.Iterator[_T]:
        return reversed(self.__backend)
