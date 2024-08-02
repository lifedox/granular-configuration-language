import json
import typing as typ
from datetime import date, datetime
from functools import partial
from uuid import UUID

from granular_configuration import Configuration


def json_default(value: typ.Any) -> typ.Any:
    """
    A factory function to be used by the `json.dump` family of functions.

    Provides serialization for the following:
    - `granular_configuration.Configuration`
    - `uuid.UUID`
    - `datetime.date`
    - `datetime.datetime
    """

    if isinstance(value, Configuration):
        return value.as_dict()
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, (date, datetime)):
        return value.isoformat()
    else:  # pragma: no cover
        return value


dumps = partial(json.dumps, default=json_default)
