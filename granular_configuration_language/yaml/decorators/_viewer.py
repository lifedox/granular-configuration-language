from __future__ import annotations

import collections.abc as tabc
import inspect
import itertools
import operator as op
import typing as typ
from collections import OrderedDict

from granular_configuration_language.yaml.decorators._base import TagConstructor

try:
    import tabulate

    can_table = True
except ImportError:  # pragma: no cover
    tabulate = None  # type: ignore[assignment]
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
    needs_root_condition: str
    eager_io: str


NULLIFY_JSON = ("interpolates", "lazy", "needs_root_condition", "eager_io")


def _interpolates(tc: TagConstructor) -> Imode:
    if tc.attributes.is_with_ref:
        return "full"  # pragma: no cover  # coverage shown by test output
    elif tc.attributes.is_without_ref:
        return "reduced"  # pragma: no cover  # coverage shown by test output
    else:
        return ""


def _needs_root_condition(tc: TagConstructor) -> str:
    condition = tc.attributes.needs_root_condition
    if condition:
        return condition.__name__  # pragma: no cover  # coverage shown by test output
    else:
        return ""


def _eager_io(tc: TagConstructor) -> str:
    eager_io = tc.attributes.eager_io
    if eager_io:
        return eager_io.__name__  # pragma: no cover  # coverage shown by test output
    else:
        return ""


def _make_row(tc: TagConstructor) -> RowType:
    return RowType(
        plugin=tc.plugin,
        category=tc.category,
        tag=tc.tag,
        type=tc.friendly_type,
        interpolates=_interpolates(tc),
        lazy="NOT_LAZY" if tc.attributes.is_not_lazy else "",
        returns=str(inspect.signature(tc.constructor).return_annotation).removeprefix("typ.").removeprefix("tabc."),
        handler=tc.constructor.__module__ + "." + tc.constructor.__name__,
        needs_root_condition=_needs_root_condition(tc),
        eager_io=_eager_io(tc),
    )


class AvailableBase:
    headers: tabc.Sequence[str]
    sort_keys: op.attrgetter
    json_remove: tabc.Sequence[str]

    def __init__(self, tags: tabc.Iterable[TagConstructor]) -> None:
        self.tags: typ.Final = tags

    def __remove_keys(self, row: RowType) -> RowType:
        keys_to_del = row.keys() - set(self.headers)

        for key in keys_to_del:
            del row[key]  # type: ignore[misc]
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

    def strip_tag(self, row: RowType) -> tuple[str, RowType]:
        tag = row.pop("tag")

        for key in self.json_remove:
            del row[key]  # type: ignore[misc]

        for key in NULLIFY_JSON:
            if (key in row) and not row[key]:  # type: ignore[literal-required]
                row[key] = None  # type: ignore[literal-required]

        return tag, row


class AvailableTags(AvailableBase):
    headers = ("category", "tag", "type", "interpolates", "lazy", "returns")
    sort_keys = op.attrgetter("category", "sort_as")
    json_remove = ("category",)

    def json(self) -> str:
        import json

        category_key = op.itemgetter("category")

        def category_group(category: str, group: tabc.Iterator[RowType]) -> tuple[str, dict[str, RowType]]:
            return category, dict(map(self.strip_tag, group))

        return json.dumps(
            dict(itertools.starmap(category_group, itertools.groupby(self.get_rows(), key=category_key))),
            sort_keys=True,
            indent=2,
        )


class AvailablePlugins(AvailableBase):
    headers = ("plugin", "category", "tag", "handler", "needs_root_condition", "eager_io")
    sort_keys = op.attrgetter("plugin", "category", "sort_as")
    json_remove = ("category", "plugin")

    def json(self) -> str:
        import json

        category_key = op.itemgetter("category")

        def category_group(category: str, group: tabc.Iterator[RowType]) -> tuple[str, dict[str, RowType]]:
            return category, dict(map(self.strip_tag, group))

        plugin_key = op.itemgetter("plugin")

        def plugin_group(plugin: str, group: tabc.Iterator[RowType]) -> tuple[str, dict[str, dict[str, RowType]]]:
            return plugin, dict(itertools.starmap(category_group, itertools.groupby(group, key=category_key)))

        return json.dumps(
            dict(itertools.starmap(plugin_group, itertools.groupby(self.get_rows(), key=plugin_key))),
            sort_keys=True,
            indent=2,
        )
