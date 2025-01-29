import inspect
import os
import typing as typ
from collections import OrderedDict
from importlib import import_module
from importlib.metadata import entry_points
from importlib.util import resolve_name
from itertools import chain, filterfalse
from operator import attrgetter, itemgetter
from pathlib import Path
from pprint import pformat

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml.decorators._base import Tag, TagConstructor
from granular_configuration_language.yaml.decorators._tag_tracker import is_not_lazy, is_with_ref, is_without_ref

ModuleName = typ.NewType("ModuleName", str)
PluginName = typ.NewType("PluginName", str)


def is_TagConstructor(obj: typ.Any) -> typ.TypeGuard[TagConstructor]:
    return isinstance(obj, TagConstructor)


def get_tags_in_module(module_name: ModuleName) -> typ.Iterator[TagConstructor]:
    return map(itemgetter(1), inspect.getmembers(import_module(module_name), is_TagConstructor))


def get_internal_tag_plugins() -> typ.Iterator[ModuleName]:
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


def get_external_tag_plugins() -> typ.Iterator[tuple[PluginName, ModuleName]]:
    return map(attrgetter("name", "module"), entry_points(group="granular-configuration-language-20-tag"))


def get_all_tag_plugins(*, disable_plugin: typ.AbstractSet[str]) -> typ.Iterator[ModuleName]:
    for module in get_internal_tag_plugins():
        yield module

    for name, module in get_external_tag_plugins():
        if name not in disable_plugin:
            yield module


class TagSet(typ.Iterable[TagConstructor], typ.Container[str]):
    def __init__(self, tags: typ.Iterable[TagConstructor]) -> None:
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

    def __iter__(self) -> typ.Iterator[TagConstructor]:
        return iter(self.__state.values())

    def has_tags(self, *tags: Tag | str) -> bool:
        return all(map(self.__contains__, tags))

    def does_not_have_tags(self, *tags: Tag | str) -> bool:
        return not any(map(self.__contains__, tags))

    def __repr__(self) -> str:
        return f"TagSet{{{','.join(sorted(self.__state.keys()))}}}"

    def pretty(self, width: int = 120, indent: int = 2) -> str:
        def get_type(tc: TagConstructor) -> str:
            attributes: set[str] = set()

            if is_with_ref(tc.constructor):
                attributes.add("interpolates")
            elif is_without_ref(tc.constructor):
                attributes.add("interpolates-reduced")

            if is_not_lazy(tc.constructor):
                attributes.add("NOT-LAZY")

            return (
                tc.friendly_type
                + (f" [{', '.join(attributes)}]" if attributes else "")
                + f" ({tc.constructor.__module__}.{tc.constructor.__name__})"
            )

        tags = {tag: get_type(tc) for tag, tc in self.__state.items()}

        return f"""TagSet{{\n {pformat(tags, width=width, indent=indent, sort_dicts=True)[1:-1]}\n}}"""


def load_tags(
    *,
    disable_plugins: typ.AbstractSet[str] = frozenset(),
    disable_tags: typ.AbstractSet[Tag | str] = frozenset(),
) -> TagSet:
    disable_plugins |= frozenset(filter(None, map(str.strip, os.getenv("G_CONFIG_DISABLE_PLUGINS", "").split(","))))
    disable_tags |= frozenset(filter(None, map(str.strip, os.getenv("G_CONFIG_DISABLE_TAGS", "").split(","))))

    return TagSet(
        filterfalse(
            disable_tags.__contains__,
            chain.from_iterable(map(get_tags_in_module, get_all_tag_plugins(disable_plugin=disable_plugins))),
        )
    )
