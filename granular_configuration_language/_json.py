from __future__ import annotations

import collections.abc as tabc
import json
import typing as typ
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime
from functools import partial, update_wrapper
from uuid import UUID

from granular_configuration_language import Configuration, LazyLoadConfiguration


def get_name(value: tabc.Callable) -> str:
    name: str | None = getattr(value, "__name__", None)
    class_type: type | None = getattr(value, "__class__", None)

    if name:
        return f"<{getattr(value, '__module__', '')}.{name}>"
    elif class_type:
        return f"<{class_type.__module__}.{class_type.__name__}()>"
    else:  # pragma: no cover
        return f"<{repr(value)}>"


def json_default(value: typ.Any) -> typ.Any:
    """A factory function to be used by the :py:func:`json.dump` family of functions.

    Provides serialization for types produced by this library's Tags.

    Explicitly:

    - :py:class:`~.Configuration` as :py:class:`dict`
    - ``!UUID``/:py:class:`uuid.UUID` as hyphenated hex string
    - ``!Date``/:py:class:`datetime.date` as :py:meth:`~datetime.date.isoformat`
    - ``!DateTime``/:py:class:`datetime.datetime` as :py:meth:`~datetime.datetime.isoformat`
    - ``!Func``/:py:class:`~collections.abc.Callable` as ``f"<{func.__module__}.{func.__name__}>"``
    - ``!Class``/:py:class:`type` as ``f"<{class.__module__}.{class.__name__}>"``
    - For niceness, :py:class:`~collections.abc.Mapping` and non-:class:`str` :py:class:`~collections.abc.Sequence`
      instances are converted to :py:class:`dict` and :py:class:`tuple`

    :param ~typing.Any value: Value being converted

    :returns: :py:func:`json.dump` compatible object
    :rtype: Any

    :raises TypeError: When an incompatible is provided, as required by :py:class:`~json.JSONEncoder`

    """
    match value:
        case Configuration():
            return value.as_dict()
        case LazyLoadConfiguration():
            return value.config.as_dict()
        case UUID():
            return str(value)
        case date() | datetime():
            return value.isoformat()
        case type():
            return f"<{value.__module__}.{value.__name__}>"
        case partial():
            return f"<{repr(value)}>"
        case Callable():
            return get_name(value)
        case Mapping():
            return dict(value)
        case Sequence():
            return tuple(value)
        case _:
            return json.JSONEncoder().default(value)


dumps = update_wrapper(partial(json.dumps, default=json_default), json.dumps)
