from __future__ import annotations

import collections.abc as tabc
import inspect
import os
import typing as typ
from importlib import import_module
from importlib.metadata import entry_points
from importlib.util import resolve_name
from itertools import chain, filterfalse, starmap
from operator import attrgetter, itemgetter
from pathlib import Path

from granular_configuration_language.yaml.decorators._base import Tag, TagConstructor
from granular_configuration_language.yaml.decorators._tag_set import TagSet

ModuleName = typ.NewType("ModuleName", str)
PluginName = typ.NewType("PluginName", str)


def is_TagConstructor(obj: typ.Any) -> typ.TypeGuard[TagConstructor]:
    return isinstance(obj, TagConstructor)


def get_tags_in_module(module_name: ModuleName, plugin_name: PluginName) -> tabc.Iterator[TagConstructor]:
    def set_plugin(tc: TagConstructor) -> TagConstructor:
        tc.set_plugin(plugin_name)
        return tc

    return map(set_plugin, map(itemgetter(1), inspect.getmembers(import_module(module_name), is_TagConstructor)))


def get_internal_tag_plugins() -> tabc.Iterator[ModuleName]:
    import granular_configuration_language.yaml._tags as tags

    tags_package = tags.__package__
    tags_module_path = Path(tags.__file__).parent
    private_sub_module_pattern = r"_[a-zA-Z]*.py"

    def get_abs_name(module_name: str) -> ModuleName:
        return ModuleName(resolve_name("." + module_name, package=tags_package))

    return map(
        get_abs_name,
        filter(
            None,
            map(
                inspect.getmodulename,
                tags_module_path.glob(private_sub_module_pattern),
            ),
        ),
    )


def get_external_tag_plugins() -> tabc.Iterator[tuple[PluginName, ModuleName]]:
    return map(attrgetter("name", "module"), entry_points(group="granular_configuration_language_20_tag"))


def get_all_tag_plugins(*, disable_plugin: tabc.Set[str]) -> tabc.Iterator[tuple[ModuleName, PluginName]]:
    builtin = PluginName("<gcl-built-in>")

    for module in get_internal_tag_plugins():
        yield module, builtin

    for name, module in get_external_tag_plugins():
        if name not in disable_plugin:
            yield module, name


def load_tags(
    *,
    disable_plugins: tabc.Set[str] = frozenset(),
    disable_tags: tabc.Set[Tag | str] = frozenset(),
) -> TagSet:
    disable_plugins |= frozenset(filter(None, map(str.strip, os.getenv("G_CONFIG_DISABLE_PLUGINS", "").split(","))))
    disable_tags |= frozenset(filter(None, map(str.strip, os.getenv("G_CONFIG_DISABLE_TAGS", "").split(","))))

    def is_disable(tc: TagConstructor) -> bool:
        return tc.tag in disable_tags

    return TagSet(
        filterfalse(
            is_disable,
            chain.from_iterable(starmap(get_tags_in_module, get_all_tag_plugins(disable_plugin=disable_plugins))),
        )
    )
