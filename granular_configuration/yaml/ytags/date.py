import sys
from granular_configuration.yaml.decorators import Tag, as_lazy, string_tag
from datetime import date, datetime

from functools import partial

if sys.version_info >= (3, 11):  # pragma: no cover
    date_fromisoformat = date.fromisoformat
    datetime_fromisoformat = datetime.fromisoformat
else:  # pragma: no cover
    from dateutil.parser import parse

    datetime_fromisoformat = partial(parse, yearfirst=True, dayfirst=False)
    date_fromisoformat = lambda value: datetime_fromisoformat(value).date()


@string_tag(Tag("!Date"))
@as_lazy
def date_handler(value: str) -> date:
    return date_fromisoformat(value)


@string_tag(Tag("!DateTime"))
@as_lazy
def datetime_handler(value: str) -> date:
    dt = datetime_fromisoformat(value)
    return dt
