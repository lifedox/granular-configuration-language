import configparser
import operator as op
import typing as typ
from collections import OrderedDict, deque
from collections.abc import MutableMapping
from functools import partial
from io import StringIO
from itertools import filterfalse, islice, starmap

from granular_configuration.exceptions import IniKeyExistAsANonMapping, IniTryToReplaceExistingKey
from granular_configuration.yaml_handler import loads as yaml_loads

consume = partial(deque, maxlen=0)
_OPH = typ.Optional[typ.Type[typ.MutableMapping]]


class IniLoader(object):
    obj_pairs_hook: typ.Type[typ.MutableMapping]
    parser: configparser.RawConfigParser

    def __init__(self, parser: configparser.RawConfigParser, *, obj_pairs_hook: _OPH = None) -> None:
        if obj_pairs_hook and issubclass(obj_pairs_hook, MutableMapping):
            self.obj_pairs_hook = obj_pairs_hook
        else:
            self.obj_pairs_hook = OrderedDict

        self.parser = parser

    def _parse_value(self, value: str) -> typ.Any:
        return yaml_loads(str(value), obj_pairs_hook=self.obj_pairs_hook)

    def _set_item(self, mapping: typ.MutableMapping, key: str, value: str) -> None:
        mapping[self._parse_value(key)] = self._parse_value(value)

    def _set_items(self, mapping: typ.MutableMapping, items: typ.Iterable[typ.Tuple[str, str]]) -> None:
        consume(starmap(partial(self._set_item, mapping), items))

    def _get_sections(self) -> typ.Iterator[str]:
        return filterfalse(op.methodcaller("__eq__", "ROOT"), self.parser.sections())

    def _get_root(self) -> typ.MutableMapping:
        if self.parser.has_section("ROOT"):
            return self._get_section("ROOT")
        else:
            return self.obj_pairs_hook()

    def _get_section(self, section: str) -> typ.MutableMapping:
        section_dict = self.obj_pairs_hook()
        self._set_items(section_dict, self.parser.items(section))
        return section_dict

    def _get_path(self, mapping: MutableMapping, keys: typ.Iterable[str]) -> typ.MutableMapping:
        current_mapping = mapping

        for key in keys:
            if not isinstance(current_mapping, MutableMapping):
                raise IniKeyExistAsANonMapping("Key found as a Non-Mapping: {}".format(".".join(keys)))
            elif key in current_mapping:
                current_mapping = current_mapping[key]
            else:
                new_mapping = self.obj_pairs_hook()
                current_mapping[key] = new_mapping
                current_mapping = new_mapping

        if isinstance(current_mapping, MutableMapping):
            return current_mapping
        else:
            raise IniKeyExistAsANonMapping("Key found as a Non-Mapping: {}".format(".".join(keys)))

    def _attach_section(self, mapping: typ.MutableMapping, section: str) -> None:
        section_dict = self._get_section(section)

        keys = section.split(".")

        placement = self._get_path(mapping, islice(keys, 0, len(keys) - 1))

        key = keys[-1]

        if key not in placement:
            placement[keys[-1]] = section_dict
        else:
            raise IniTryToReplaceExistingKey("Key already exists: {}".format(section))

    def read(self) -> typ.MutableMapping:
        config_dict = self._get_root()

        consume(map(partial(self._attach_section, config_dict), self._get_sections()))

        return config_dict


def loads(config_str: str, obj_pairs_hook: _OPH = None) -> typ.Any:
    parser = configparser.RawConfigParser()
    parser.optionxform = str  # type: ignore
    parser.read_file(StringIO(config_str))

    return IniLoader(parser, obj_pairs_hook=obj_pairs_hook).read()
