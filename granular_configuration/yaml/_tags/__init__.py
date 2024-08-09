import inspect
import typing as typ
from itertools import chain
from pathlib import Path

from granular_configuration.yaml.decorators._tag_loader import get_tags

PRIVATE_SUB_MODULE_REGEX: typ.Final = r"_[a-zA-Z]*.py"
add_package_prefix: typ.Final = (str(__package__) + ".").__add__

handlers: typ.Final = frozenset(
    chain.from_iterable(
        map(
            get_tags,
            map(
                add_package_prefix,
                filter(
                    None,
                    map(
                        inspect.getmodulename,
                        Path(__file__).parent.glob(PRIVATE_SUB_MODULE_REGEX),
                    ),
                ),
            ),
        )
    )
)
