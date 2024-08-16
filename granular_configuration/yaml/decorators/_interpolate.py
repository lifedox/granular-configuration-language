import re
import typing as typ
from functools import wraps
from html import unescape

from granular_configuration._utils import get_environment_variable
from granular_configuration.yaml.classes import Root
from granular_configuration.yaml.decorators.ref import resolve_json_ref

SUB_PATTERN: typ.Pattern[str] = re.compile(r"(\$\{(?P<contents>.*?)\})")

_P = typ.ParamSpec("_P")
_RT = typ.TypeVar("_RT")


def load_sub(root: Root, *, contents: str) -> str:
    if root and contents.startswith("$") or contents.startswith("/"):
        value = resolve_json_ref(contents, root)
        if isinstance(value, str):
            return value
        elif isinstance(value, (typ.Mapping, typ.Sequence)):
            return repr(value)
        else:
            return str(value)
    elif contents.startswith("&") and contents.endswith(";"):
        return unescape(contents)
    else:
        return get_environment_variable(*contents.split(":-", maxsplit=1))


def interpolate(value: str, root: Root) -> str:
    return SUB_PATTERN.sub(lambda x: load_sub(root, **x.groupdict()), value)


def interpolate_value_with_sub_rules(
    func: typ.Callable[typ.Concatenate[str, Root, _P], _RT]
) -> typ.Callable[typ.Concatenate[str, Root, _P], _RT]:
    @wraps(func)
    def lazy_wrapper(value: str, root: Root, *args: _P.args, **kwargs: _P.kwargs) -> _RT:
        return func(interpolate(value, root), root, *args, **kwargs)

    return lazy_wrapper


def interpolate_value_without_ref(
    func: typ.Callable[typ.Concatenate[str, _P], _RT]
) -> typ.Callable[typ.Concatenate[str, _P], _RT]:
    @wraps(func)
    def lazy_wrapper(value: str, *args: _P.args, **kwargs: _P.kwargs) -> _RT:
        return func(interpolate(value, None), *args, **kwargs)

    return lazy_wrapper
