import inspect
import operator as op
import typing as typ
from importlib.metadata import entry_points
from itertools import chain
from pathlib import Path

from granular_configuration.yaml.decorators._tag_loader import get_tags


PRIVATE_SUB_MODULE_REGEX: typ.Final = r"_[a-zA-Z]*.py"
add_package_prefix: typ.Final = (str(__package__) + ".").__add__

internal_tags = map(
    add_package_prefix,
    filter(
        None,
        map(
            inspect.getmodulename,
            Path(__file__).parent.glob(PRIVATE_SUB_MODULE_REGEX),
        ),
    ),
)
external_tag = map(op.attrgetter("module"), entry_points(group="gc20tag"))


handlers: typ.Final = frozenset(
    chain.from_iterable(
        map(
            get_tags,
            chain(internal_tags, external_tag),
        )
    )
)
