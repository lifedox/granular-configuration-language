from __future__ import annotations

import collections.abc as tabc


class BasePathPart(str):
    __slots__ = ()


class BasePath(tuple[BasePathPart]):
    __slots__ = ()


def read_base_path(base_path: str | tabc.Sequence[str] | None) -> BasePath:
    if isinstance(base_path, str):
        if base_path.startswith("/"):
            return BasePath(map(BasePathPart, filter(None, base_path.split("/"))))
        else:
            return BasePath((BasePathPart(base_path),))
    elif base_path:
        return BasePath(map(BasePathPart, base_path))
    else:
        return BasePath()
