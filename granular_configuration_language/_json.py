import inspect
import json
import typing as typ
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from functools import partial, update_wrapper
from uuid import UUID

from granular_configuration_language import Configuration


def get_name(value: typ.Callable) -> str:
    try:
        return f"<{value.__module__}.{value.__name__}>"
    except Exception:  # pragma: no cover
        return f"<{repr(value)}>"


def json_default(value: typ.Any) -> typ.Any:
    """
    A factory function to be used by the :py:func:`json.dump` family of functions.

    Provides serialization for types produced by this library's Tags.

    Explicitly:

    * :py:class:`~.Configuration` as :py:class:`dict`

    * :code:`!UUID`/:py:class:`uuid.UUID` as hyphenated hex string

    * :code:`!Date`/:py:class:`datetime.date` as :py:meth:`datetime.date.isoformat`

    * :code:`!DateTime`/:py:class:`datetime.datetime` as :py:meth:`datetime.datetime.isoformat`

    * :code:`!Func`/:py:class:`Callable` as :code:`f"<{func.__module__}.{func.__name__}>"`

    * :code:`!Class`/:code:`class` as :code:`f"<{class.__module__}.{class.__name__}>"`

    * For niceness, :py:class:`~collections.abc.Mapping` and non-:class:`str`
      :py:class:`~collections.abc.Sequence` instances are converted to :py:class:`dict` and :py:class:`tuple`

    :param value: Value being converted
    :type value: ~typing.Any
    :raises TypeError: When an incompatible is provided, as required by :py:class:`~json.JSONEncoder`
    :return: :py:func:`json.dump` compatible object
    :rtype: Any
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
    elif isinstance(value, Mapping):
        return dict(value)
    elif isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    else:
        return json.JSONEncoder().default(value)


dumps = update_wrapper(partial(json.dumps, default=json_default), json.dumps)
