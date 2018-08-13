from __future__ import print_function
from io import StringIO
from collections import OrderedDict, MutableMapping, deque
from six.moves import map, filterfalse, configparser
from six import text_type
from functools import partial
from itertools import starmap, islice
import operator as op

from granular_configuration.yaml_handler import loads as yaml_loads
from granular_configuration.exceptions import IniKeyExistAsANonMapping, IniTryToReplaceExistingKey

consume = partial(deque, maxlen=0)


class IniLoader(object):
    def __init__(self, parser, obj_pairs_hook=None):
        if obj_pairs_hook and issubclass(obj_pairs_hook, MutableMapping):
            self.obj_pairs_hook = obj_pairs_hook
        else:
            self.obj_pairs_hook = OrderedDict

        self.parser = parser

    def _parse_value(self, value):
        return yaml_loads(str(value), obj_pairs_hook=self.obj_pairs_hook)

    def _set_item(self, mapping, key, value):
        mapping[self._parse_value(key)] = self._parse_value(value)

    def _set_items(self, mapping, items):
        consume(starmap(partial(self._set_item, mapping), items))

    def _get_sections(self):
        return filterfalse(op.methodcaller("__eq__", "ROOT"), self.parser.sections())

    def _get_root(self):
        if self.parser.has_section("ROOT"):
            return self._get_section("ROOT")
        else:
            return self.obj_pairs_hook()

    def _get_section(self, section):
        section_dict = self.obj_pairs_hook()
        self._set_items(section_dict, self.parser.items(section))
        return section_dict

    def _get_path(self, mapping, keys):
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

    def _attach_section(self, mapping, section):
        section_dict = self._get_section(section)

        keys = section.split(".")

        placement = self._get_path(mapping, islice(keys, 0, len(keys) - 1))

        key = keys[-1]

        if key not in placement:
            placement[keys[-1]] = section_dict
        else:
            raise IniTryToReplaceExistingKey("Key already exists: {}".format(section))

    def read(self):
        config_dict = self._get_root()

        consume(map(partial(self._attach_section, config_dict), self._get_sections()))

        return config_dict


def loads(ini_str, obj_pairs_hook=None):
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    parser.readfp(StringIO(text_type(ini_str)))

    return IniLoader(parser, obj_pairs_hook).read()
