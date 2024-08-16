import inspect
import json
import typing as typ
from datetime import date, datetime
from functools import partial
from uuid import UUID

from granular_configuration import Configuration


def get_name(value: typ.Callable) -> str:
    try:
        return f"<{value.__module__}.{value.__name__}>"
    except Exception:  # pragma: no cover
        return f"<{repr(value)}>"


def json_default(value: typ.Any) -> typ.Any:
    """
    A factory function to be used by the `json.dump` family of functions.

    Provides serialization for types produced by this library's Tags.

    Explicitly:
    - `granular_configuration.Configuration` as `dict`
    - `!UUID` -- `uuid.UUID` as hyphenated hex string
    - `!Date` -- `datetime.date` as `isoformat`
    - `!DateTime` -- `datetime.datetime` as `isoformat`
    - `!Func` -- callable as `f"<{func.__module__}.{func.__name__}>"`
    - `!Class` -- class as `f"<{class.__module__}.{class.__name__}>"`
    """

    if isinstance(value, Configuration):
        return value.as_dict()
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, (date, datetime)):
        return value.isoformat()
    elif inspect.isclass(value):
        return get_name(value)
    elif isinstance(value, partial):
        return f"<{repr(value)}>"
    elif callable(value):
        return get_name(value)
    else:  # pragma: no cover
        return value


dumps = partial(json.dumps, default=json_default)
