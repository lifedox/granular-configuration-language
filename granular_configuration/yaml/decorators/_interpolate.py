import re
import typing as typ
import warnings
from functools import wraps
from html import unescape

from granular_configuration._utils import get_environment_variable
from granular_configuration.exceptions import InterpolationWarning
from granular_configuration.yaml.classes import Root
from granular_configuration.yaml.decorators._tag_tracker import track_as_with_ref, track_as_without_ref
from granular_configuration.yaml.decorators.ref import resolve_json_ref

_P = typ.ParamSpec("_P")
_RT = typ.TypeVar("_RT")


def curly_sub(root: Root, *, contents: str) -> str:
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


def round_sub(root: Root, *, contents: str) -> str:
    warnings.warn("`!Sub $()` is reserved", InterpolationWarning)
    return "$(" + contents + ")"


def square_sub(root: Root, *, contents: str) -> str:
    warnings.warn("`!Sub $[]` is reserved", InterpolationWarning)
    return "$[" + contents + "]"


SUB_PATTERNS: typ.Final[typ.Sequence[tuple[typ.Callable, typ.Pattern[str]]]] = (
    (round_sub, re.compile(r"(\$\((?P<contents>.*?)\))")),
    (square_sub, re.compile(r"(\$\[(?P<contents>.*?)\])")),
    (curly_sub, re.compile(r"(\$\{(?P<contents>.*?)\})")),
)


def interpolate(value: str, root: Root) -> str:
    for sub, pat in SUB_PATTERNS:
        value = pat.sub(lambda x: sub(root, **x.groupdict()), value)
    return value


def interpolate_value_with_ref(
    func: typ.Callable[typ.Concatenate[str, Root, _P], _RT]
) -> typ.Callable[typ.Concatenate[str, Root, _P], _RT]:
    @wraps(func)
    def lazy_wrapper(value: str, root: Root, *args: _P.args, **kwargs: _P.kwargs) -> _RT:
        return func(interpolate(value, root), root, *args, **kwargs)

    track_as_with_ref(func)
    return lazy_wrapper


def interpolate_value_without_ref(
    func: typ.Callable[typ.Concatenate[str, _P], _RT]
) -> typ.Callable[typ.Concatenate[str, _P], _RT]:
    @wraps(func)
    def lazy_wrapper(value: str, *args: _P.args, **kwargs: _P.kwargs) -> _RT:
        return func(interpolate(value, None), *args, **kwargs)

    track_as_without_ref(func)
    return lazy_wrapper
