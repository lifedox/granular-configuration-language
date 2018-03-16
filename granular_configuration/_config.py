from __future__ import print_function, absolute_import
from collections import Mapping, deque, OrderedDict
import os
from itertools import product, groupby, chain, starmap, islice
from six import iteritems
from six.moves import map, filter, zip_longest
from functools import partial, reduce
from granular_configuration.yaml_handler import loads

consume = partial(deque, maxlen=0)

class Configuration(dict):
    def __init__(self, *arg, **kwargs):
        super(Configuration, self).__init__(*arg, **kwargs)
        self.__dict__.update(self)

    def __setitem__(self, key, value):
        setattr(self, key, value)
        return super(Configuration, self).__setitem__(key, value)

def _load_file(filename):
    try:
        with open(filename, "r") as f:
            return loads(f.read(), obj_pairs_hook=Configuration)
    except Exception as e:
        raise ValueError('Problem in file "{}": {}'.format(filename, e))

def _build_configuration(locations):
    def _recursive_build_config(base_dict, from_dict):
        assert isinstance(base_dict, Configuration)
        assert isinstance(from_dict, Mapping)

        for key, value in iteritems(from_dict):
            if isinstance(value, dict) and (key in base_dict) and isinstance(base_dict[key], dict):
                new_dict = base_dict[key]
                _recursive_build_config(new_dict, value)
                value = new_dict

            base_dict[key] = value

    available_configs = map(_load_file, locations)
    valid_configs = filter(lambda config: isinstance(config, dict), available_configs)

    base_conf = Configuration()
    consume(map(partial(_recursive_build_config, base_conf), valid_configs))

    return base_conf

def _get_files_from_locations(filenames=None, directories=None, files=None):
    if not filenames or not directories:
        filenames = []
        directories = []

    files = set(files) if files else set()

    return OrderedDict(
        zip_longest(chain(
                chain.from_iterable(map(
                    lambda a: islice(filter(os.path.isfile,
                                    starmap(os.path.join, a[1])),
                                     1),
                    groupby(product(directories, filenames), key=lambda a: a[0]))),
                filter(os.path.isfile, files)),
            [])
        ).keys()


class ConfigurationLocations():
    def __init__(self, filenames=None, directories=None, files=None):
        if files and (filenames or directories):
            raise ValueError("files cannot be defined with filenames and directories.")
        elif bool(filenames) ^ bool(directories):
            raise ValueError("filenames and directories are a required pair.")

        self.filenames = filenames
        self.directories = directories
        self.files = files

    def get_locations(self):
        return _get_files_from_locations(filenames=self.filenames,
                                         directories=self.directories,
                                         files=self.files)

def _get_all_unique_locations(locations):
    return OrderedDict(
        zip_longest(
            chain.from_iterable(map(ConfigurationLocations.get_locations, locations)),
            [])
    ).keys()

class LazyLoadConfiguration(object):
    def __init__(self, *locations, **kwargs):
        base_path = kwargs.get("base_path")
        self._base_path = base_path if base_path else []
        self._config = None
        self._locations = locations
        if not any(map(lambda loc: isinstance(loc, ConfigurationLocations), locations)):
            raise ValueError("locations be of type ConfigurationLocations.")

    def get(self, *args, **kwargs):
        return self._config.get(*args, **kwargs)

    def __getattr__(self, name):
        if self._config is None:
            self.load_configure()

        return getattr(self._config, name)

    def load_configure(self):
        if self._config is None:
            self._config = reduce(lambda dic, key: dic[key],
                                  self._base_path,
                                  _build_configuration(_get_all_unique_locations(self._locations)))
            self._locations = None
            self._base_path = None

