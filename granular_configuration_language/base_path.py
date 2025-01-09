import typing as typ


class BasePathPart(str):
    pass


class BasePath(tuple[BasePathPart]):
    pass


def read_base_path(base_path: str | typ.Sequence[str] | None) -> BasePath:
    if isinstance(base_path, str):
        if base_path.startswith("/"):
            return BasePath(map(BasePathPart, filter(None, base_path.split("/"))))
        else:
            return BasePath((BasePathPart(base_path),))
    elif base_path:
        return BasePath(map(BasePathPart, base_path))
    else:
        return BasePath()