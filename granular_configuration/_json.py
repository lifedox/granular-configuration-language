import typing as typ
from datetime import date, datetime
from uuid import UUID

from granular_configuration import Configuration


def json_default(value: typ.Any) -> typ.Any:
    if isinstance(value, Configuration):
        return value.as_dict()
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, (date, datetime)):
        return value.isoformat()
    else:  # pragma: no cover
        return value
