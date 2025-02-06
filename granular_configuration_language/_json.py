import collections.abc as tabc
import inspect
import json
import typing as typ
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from functools import partial, update_wrapper
from uuid import UUID

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language.proxy import SafeConfigurationProxy


def get_name(value: tabc.Callable) -> str:
    try:
        return f"<{value.__module__}.{value.__name__}>"
    except Exception:  # pragma: no cover
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

    if isinstance(value, Configuration):
        return value.as_dict()
    elif isinstance(value, LazyLoadConfiguration):
        return value.config.as_dict()
    elif isinstance(value, SafeConfigurationProxy):
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
    elif isinstance(value, Mapping):
        return dict(value)
    elif isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    else:
        return json.JSONEncoder().default(value)


dumps = update_wrapper(partial(json.dumps, default=json_default), json.dumps)
