from __future__ import print_function, absolute_import
from collections import deque, OrderedDict, MutableMapping
import os
import copy
from itertools import product, groupby, chain, starmap, islice
from six import iteritems
from six.moves import map, filter, zip_longest
from functools import partial, reduce
from granular_configuration.yaml_handler import loads, Placeholder, LazyEval
from granular_configuration.exceptions import PlaceholderConfigurationError

consume = partial(deque, maxlen=0)

class Configuration(MutableMapping):
    def __init__(self, *arg, **kwargs):
        self.__data = dict()
        consume(starmap(self.__setitem__, iteritems(dict(*arg, **kwargs))))

        self.__parent_generate_name = None
        self.__name = None

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __delitem__(self, key):
        return self.__data.__delitem__(key)

    def __generate_name(self, attribute=None):
        if callable(self.__parent_generate_name):
            for name in self.__parent_generate_name(): # pylint: disable=not-callable
                yield name
        if self.__name:
            yield self.__name
        if attribute:
            yield attribute

    def __get_name(self, attribute=None):
        return ".".join(self.__generate_name(attribute))

    def __setitem__(self, key, value):
        if isinstance(value, Configuration):
            value.__name = key
            value.__parent_generate_name = self.__generate_name
        self.__data[key] = value

    def __getitem__(self, name):
        value = self.__data[name]
        if isinstance(value, Placeholder):
            raise PlaceholderConfigurationError(
                'Configuration expects "{}" to be overwritten. Message: "{}"'.format(self.__get_name(name), value))
        elif isinstance(value, LazyEval):
            new_value = value.run()
            self[name] = new_value
            return new_value
        else:
            return value

    def get(self, key, default=None):
        return self[key] if self.exists(key) else default

    def __getattr__(self, name):
        if name not in self:
            raise AttributeError('Configuration value "{}" does not exist'.format(self.__get_name(name)))

        return self[name]

    def __repr__(self):
        return repr(self.__data)

    def __contains__(self, key):
        return key in self.__data

    def exists(self, key):
        return (key in self.__data) and not isinstance(self.__data[key], Placeholder)

    def as_dict(self):
        return dict(starmap(lambda key, value: (key, value.as_dict() if isinstance(value, Configuration) else value),
                            iteritems(self)))

    def __deepcopy__(self, memo):
        other = Configuration()
        memo[id(self)] = other
        for key, value in iteritems(self.__data):
            other[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return other

    def _raw_items(self):
        return iteritems(self.__data)

    def __getnewargs__(self):
        return tuple(self.items())

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)

    @property
    def __class__(self):
        return _ConDict


class _ConDict(dict, Configuration): # pylint: disable=too-many-ancestors
    pass

def _unique_ordered_iterable(iter):
    return OrderedDict(zip_longest(iter, [])).keys()

def _load_file(filename):
    try:
        with open(filename, "r") as f:
            return loads(f.read(), obj_pairs_hook=Configuration)
    except Exception as e:
        raise ValueError('Problem in file "{}": {}'.format(filename, e))

def _build_configuration(locations):
    def _recursive_build_config(base_dict, from_dict):
        assert isinstance(base_dict, Configuration)
        assert isinstance(from_dict, Configuration)

        for key, value in from_dict._raw_items():
            if isinstance(value, Configuration) and (key in base_dict):
                if not base_dict.exists(key):
                    base_dict[key] = Configuration()
                elif not isinstance(base_dict[key], Configuration):
                    continue

                new_dict = base_dict[key]
                _recursive_build_config(new_dict, value)
                value = new_dict

            base_dict[key] = value

    available_configs = map(_load_file, locations)
    valid_configs = filter(lambda config: isinstance(config, Configuration), available_configs)

    base_conf = Configuration()
    consume(map(partial(_recursive_build_config, base_conf), valid_configs))

    return base_conf

def _get_files_from_locations(filenames=None, directories=None, files=None):
    if not filenames or not directories:
        filenames = []
        directories = []

    files = _unique_ordered_iterable(files) if files else []

    return _unique_ordered_iterable(
        chain(
            chain.from_iterable(map(
                lambda a: islice(filter(os.path.isfile,
                                        starmap(os.path.join, a[1])),
                                 1),
                groupby(product(directories, filenames), key=lambda a: a[0]))),
            filter(os.path.isfile, files)
        ))


class ConfigurationLocations(object):
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

class ConfigurationFiles(ConfigurationLocations):
    def __init__(self, files):
        super(ConfigurationFiles, self).__init__(filenames=None,
                                                 directories=None,
                                                 files=files)

class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames, directories):
        super(ConfigurationMultiNamedFiles, self).__init__(filenames=filenames,
                                                           directories=directories,
                                                           files=None)

def _get_all_unique_locations(locations):
    return _unique_ordered_iterable(chain.from_iterable(map(ConfigurationLocations.get_locations, locations)))
class LazyLoadConfiguration(object):
    def __init__(self, *load_order_location, **kwargs):
        base_path = kwargs.get("base_path")
        self._base_path = base_path if base_path else []
        self._config = None
        self._locations = load_order_location
        if not any(map(lambda loc: isinstance(loc, ConfigurationLocations), load_order_location)):
            raise ValueError("locations be of type ConfigurationLocations.")

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

