from __future__ import annotations

import collections.abc as tabc
import inspect
import itertools
import operator as op
import typing as typ
from collections import OrderedDict

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml.decorators._base import Tag, TagConstructor
from granular_configuration_language.yaml.decorators._tag_tracker import is_not_lazy, is_with_ref, is_without_ref

try:
    import tabulate
except ImportError:  # pragma: no cover
    tabulate = None  # type: ignore

Imode = typ.Literal["full"] | typ.Literal["reduced"] | typ.Literal[""]


class RowType(typ.TypedDict, total=False):
    category: str
    tag: str
    type: str
    interpolates: Imode
    lazy: typ.Literal["NOT_LAZY"] | typ.Literal[""]
    returns: str
    handler: str


def _interpolates(tc: TagConstructor) -> Imode:
    if is_with_ref(tc.constructor):
        return "full"
    elif is_without_ref(tc.constructor):
        return "reduced"
    else:
        return ""


def _make_row(tc: TagConstructor) -> RowType:
    return RowType(
        category=tc.category,
        tag=tc.tag,
        type=tc.friendly_type,
        interpolates=_interpolates(tc),
        lazy="NOT_LAZY" if is_not_lazy(tc.constructor) else "",
        returns=str(inspect.signature(tc.constructor).return_annotation).removeprefix("typ.").removeprefix("tabc."),
        handler=tc.constructor.__module__ + "." + tc.constructor.__name__,
    )


class TagSet(tabc.Iterable[TagConstructor], typ.Container[str]):
    def __init__(self, tags: tabc.Iterable[TagConstructor]) -> None:
        self.__state: OrderedDict[Tag, TagConstructor] = OrderedDict()

        for tc in tags:
            tag = tc.tag
            if tag in self.__state:
                raise ErrorWhileLoadingTags(
                    f"Tag is already defined. `{repr(tc)}` attempted to replace `{repr(self.__state[tag])}`"
                )
            else:
                self.__state[tag] = tc

    def __contains__(self, x: typ.Any) -> bool:
        return x in self.__state

    def __iter__(self) -> tabc.Iterator[TagConstructor]:
        return iter(self.__state.values())

    def __repr__(self) -> str:
        return f"TagSet{{{','.join(sorted(self.__state.keys()))}}}"

    def has_tags(self, *tags: Tag | str) -> bool:
        return all(map(self.__contains__, tags))

    def does_not_have_tags(self, *tags: Tag | str) -> bool:
        return not any(map(self.__contains__, tags))

    def get_subset(self, *select: str) -> TagSet:
        def subset() -> tabc.Iterator[TagConstructor]:
            for tag in self:
                if tag.tag in select:
                    yield tag

        return TagSet(subset())

    @property
    def headers(self) -> OrderedDict[str, str]:
        return OrderedDict(zip(*itertools.tee(typ.get_type_hints(RowType).keys(), 2)))

    def get_rows(self) -> tabc.Iterator[RowType]:
        return map(_make_row, sorted(self, key=op.attrgetter("category", "sort_as")))

    @property
    def can_table(self) -> bool:
        return bool(tabulate)

    def table(self, *, _force_missing: bool = False) -> str:
        if tabulate and not _force_missing:
            return tabulate.tabulate(self.get_rows(), headers=self.headers)
        else:
            return """\
The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies"""

    def csv(self) -> str:
        import csv
        import io

        with io.StringIO(newline="") as output:
            writer = csv.DictWriter(output, self.headers.keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.get_rows())
            return output.getvalue()[:-1]

    def json(self) -> str:
        import json

        def strip_tag(row: RowType) -> tuple[str, RowType]:
            tag = row.pop("tag")
            del row["category"]
            return tag, row

        def handle_group(category: str, group: tabc.Iterator[RowType]) -> tuple[str, dict[str, RowType]]:
            return category, dict(map(strip_tag, group))

        return json.dumps(
            dict(itertools.starmap(handle_group, itertools.groupby(self.get_rows(), key=op.itemgetter("category")))),
            sort_keys=True,
            indent=2,
        )
