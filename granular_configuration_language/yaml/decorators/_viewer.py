from __future__ import annotations

import collections.abc as tabc
import inspect
import itertools
import operator as op
import typing as typ
from collections import OrderedDict

from granular_configuration_language.yaml.decorators._base import TagConstructor
from granular_configuration_language.yaml.decorators._tag_tracker import is_not_lazy, is_with_ref, is_without_ref

try:
    import tabulate

    can_table = True
except ImportError:  # pragma: no cover
    tabulate = None  # type: ignore
    can_table = False


Imode = typ.Literal["full"] | typ.Literal["reduced"] | typ.Literal[""]


class RowType(typ.TypedDict, total=False):
    plugin: str
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
        plugin=tc.plugin,
        category=tc.category,
        tag=tc.tag,
        type=tc.friendly_type,
        interpolates=_interpolates(tc),
        lazy="NOT_LAZY" if is_not_lazy(tc.constructor) else "",
        returns=str(inspect.signature(tc.constructor).return_annotation).removeprefix("typ.").removeprefix("tabc."),
        handler=tc.constructor.__module__ + "." + tc.constructor.__name__,
    )


class AvailableBase:
    headers: tabc.Sequence[str]
    sort_keys: op.attrgetter

    def __init__(self, tags: tabc.Iterable[TagConstructor]) -> None:
        self.tags: typ.Final = tags

    def __remove_keys(self, row: RowType) -> RowType:
        keys_to_del = row.keys() - set(self.headers)

        for key in keys_to_del:
            del row[key]  # type: ignore
        return row

    def get_rows(self) -> tabc.Iterator[RowType]:
        return map(self.__remove_keys, map(_make_row, sorted(self.tags, key=self.sort_keys)))

    def table(self, *, _force_missing: bool = False) -> str:
        if tabulate and not _force_missing:
            return tabulate.tabulate(self.get_rows(), headers=OrderedDict(zip(self.headers, self.headers)))
        else:
            return """\
The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies"""

    def csv(self) -> str:
        import csv
        import io

        with io.StringIO(newline="") as output:
            writer = csv.DictWriter(output, self.headers, lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.get_rows())
            return output.getvalue()[:-1]


class AvailableTags(AvailableBase):
    headers = ("category", "tag", "type", "interpolates", "lazy", "returns")
    sort_keys = op.attrgetter("category", "sort_as")

    def json(self) -> str:
        import json

        def strip_tag(row: RowType) -> tuple[str, RowType]:
            tag = row.pop("tag")
            del row["category"]
            return tag, row

        category_key = op.itemgetter("category")

        def category_group(category: str, group: tabc.Iterator[RowType]) -> tuple[str, dict[str, RowType]]:
            return category, dict(map(strip_tag, group))

        return json.dumps(
            dict(itertools.starmap(category_group, itertools.groupby(self.get_rows(), key=category_key))),
            sort_keys=True,
            indent=2,
        )


class AvailablePlugins(AvailableBase):
    headers = ("plugin", "category", "tag", "handler")
    sort_keys = op.attrgetter("plugin", "category", "sort_as")

    def json(self) -> str:
        import json

        def strip_tag(row: RowType) -> tuple[str, RowType]:
            tag = row.pop("tag")
            del row["category"]
            return tag, row

        category_key = op.itemgetter("category")

        def category_group(category: str, group: tabc.Iterator[RowType]) -> tuple[str, dict[str, RowType]]:
            return category, dict(map(strip_tag, group))

        plugin_key = op.itemgetter("plugin")

        def plugin_group(plugin: str, group: tabc.Iterator[RowType]) -> tuple[str, dict[str, dict[str, RowType]]]:
            return plugin, dict(itertools.starmap(category_group, itertools.groupby(group, key=category_key)))

        return json.dumps(
            dict(itertools.starmap(plugin_group, itertools.groupby(self.get_rows(), key=plugin_key))),
            sort_keys=True,
            indent=2,
        )
