import typing as typ

BasePath = typ.NewType("BasePath", tuple[str])


def read_base_path(base_path: str | typ.Sequence[str] | None) -> BasePath:
    if isinstance(base_path, str):
        result: typ.Sequence[str] = (base_path,)
    elif base_path:
        result = base_path if isinstance(base_path, tuple) else tuple(base_path)
    else:
        result = tuple()
    return typ.cast(BasePath, result)
