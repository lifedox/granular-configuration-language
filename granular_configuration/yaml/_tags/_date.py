import sys
from datetime import date, datetime
from functools import partial

from granular_configuration.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag

if sys.version_info >= (3, 11):
    date_fromisoformat = date.fromisoformat
    datetime_fromisoformat = datetime.fromisoformat
else:  # if sys.version_info
    from dateutil.parser import parse

    datetime_fromisoformat = partial(parse, yearfirst=True, dayfirst=False)
    date_fromisoformat = lambda value: datetime_fromisoformat(value).date()


@string_tag(Tag("!Date"))
@as_lazy
@interpolate_value_without_ref
def date_handler(value: str) -> date:
    return date_fromisoformat(value)


@string_tag(Tag("!DateTime"))
@as_lazy
@interpolate_value_without_ref
def datetime_handler(value: str) -> date:
    dt = datetime_fromisoformat(value)
    return dt
