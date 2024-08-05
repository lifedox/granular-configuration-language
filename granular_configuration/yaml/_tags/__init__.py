import inspect
import typing as typ
from itertools import chain
from pathlib import Path

from granular_configuration.yaml.decorators._tag_loader import get_tags

package_prefix = (str(__package__) + ".").__add__

handlers: typ.Final = frozenset(
    chain.from_iterable(
        map(
            get_tags,
            map(
                package_prefix,
                map(
                    inspect.getmodulename,  # type: ignore Pylance is being wrong
                    Path(__file__).parent.glob(r"_[a-zA-Z]*.py"),
                ),
            ),
        )
    )
)
