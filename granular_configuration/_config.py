from __future__ import print_function, absolute_import
from collections import deque, MutableMapping, Mapping
import os
import copy
import operator as op
from itertools import product, groupby, chain, starmap, islice
from six import iteritems, string_types
from six.moves import map, filter, filterfalse
from functools import partial, reduce
from contextlib import contextmanager

from granular_configuration.yaml_handler import Placeholder, LazyEval
from granular_configuration._load import load_file
from granular_configuration.exceptions import PlaceholderConfigurationError
from granular_configuration.utils import OrderedSet

consume = partial(deque, maxlen=0)


class Patch(Mapping):
    def __init__(self, patch_map, parent=None):
        if not isinstance(patch_map, Mapping):
            raise TypeError("Patch expected a Mapping as input")

        self._patch = {
            key: Configuration(value) if isinstance(value, Mapping) and not isinstance(value, Configuration) else value
            for key, value in iteritems(patch_map)
        }
        self._alive = True
        self._parent = parent

    def __getitem__(self, name):
        return self._patch[name]

    def __iter__(self):
        return iter(self._patch)

    def __len__(self):
        return len(self._patch)

    def __hash__(self):
        return id(self)

    @property
    def alive(self):
        if self._parent is not None:
            return self._parent.alive
        else:
            return self._alive

    def kill(self):
        return self._alive

    def make_child(self, name):
        return self.__class__(self._patch[name], parent=self)


class Configuration(MutableMapping):
    def __init__(self, *arg, **kwargs):
        self.__data = dict()
        consume(starmap(self.__setitem__, iteritems(dict(*arg, **kwargs))))

        self.__parent_generate_name = None
        self.__name = None

        self.__patches = OrderedSet()

    def __iter__(self):
        if self.__has_patches():
            return iter(OrderedSet(chain(self.__data, chain.from_iterable(self.__iter_patches()))))
        else:
            return iter(self.__data)

    def __len__(self):
        if self.__has_patches():
            return len(OrderedSet(chain(self.__data, chain.from_iterable(self.__iter_patches()))))
        else:
            return len(self.__data)

    def __delitem__(self, key):
        return self.__data.__delitem__(key)

    def __generate_name(self, attribute=None):
        if callable(self.__parent_generate_name):
            for name in self.__parent_generate_name():  # pylint: disable=not-callable
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

    def __get_from_patches(self, name):
        for patch in self.__iter_patches():
            if name in patch:
                return patch[name]
        return self.__data[name]

    def __get_item(self, name):
        if self.__has_patches():
            value = self.__get_from_patches(name)

            if isinstance(value, Configuration):
                consume(map(value.__add_patch, self.__get_child_patches(name)))

        else:
            value = self.__data[name]
        return value

    def __getitem__(self, name):
        value = self.__get_item(name)
        if isinstance(value, Placeholder):
            raise PlaceholderConfigurationError(
                'Configuration expects "{}" to be overwritten. Message: "{}"'.format(self.__get_name(name), value)
            )
        elif isinstance(value, LazyEval):
            new_value = value.run()
            self[name] = new_value
            return new_value
        else:
            return value

    def get(self, key, default=None):
        return self[key] if self.exists(key) else default

    def __getattr__(self, name):
        """
        Provides potentially cleaner path as an alternative to __getitem__.
        Throws AttributeError instead of KeyError, as compared to __getitem__ when an attribute is not present.
        """
        if name not in self:
            raise AttributeError('Configuration value "{}" does not exist'.format(self.__get_name(name)))

        return self[name]

    def __repr__(self):
        if self.__has_patches():
            return repr(self.as_dict())
        else:
            return repr(self.__data)

    def __contains__(self, key):
        return key in self.__data or (
            self.__has_patches() and any(map(op.methodcaller("__contains__", key), self.__iter_patches()))
        )

    def exists(self, key):
        """
        Checks that a key exists and is not a Placeholder
        """
        return (key in self) and not isinstance(self.__get_item(key), Placeholder)

    def as_dict(self):
        """
        Returns the Configuration settings as standard Python dict.
        Nested Configartion object will also be converted.
        This will evaluated all lazy tag functions and throw an exception on Placeholders.
        """
        return dict(
            starmap(
                lambda key, value: (key, value.as_dict() if isinstance(value, Configuration) else value),
                iteritems(self),
            )
        )

    def __deepcopy__(self, memo):
        other = Configuration()
        memo[id(self)] = other
        for key, value in iteritems(self.__data):
            other[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return other

    def __copy__(self):
        return copy.deepcopy(self)

    copy = __copy__

    def _raw_items(self):
        return map(lambda key: (key, self.__get_item(key)), self)

    def __getnewargs__(self):
        return tuple(self.items())

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)

    @property
    def __class__(self):
        return _ConDict

    def __add_patch(self, patch):
        self.__patches.add(patch)

    def __has_patches(self):
        for killed in tuple(filterfalse(op.attrgetter("alive"), self.__patches)):
            self.__patches.remove(killed)
        return bool(self.__patches)

    def __iter_patches(self):
        return reversed(self.__patches)

    @contextmanager
    def patch(self, patch_map):
        patch = Patch(patch_map)
        self.__add_patch(patch)
        yield
        patch.kill()
        self.__patches.remove(patch)

    def __get_child_patches(self, name):
        return map(op.methodcaller("make_child", name), filter(op.methodcaller("__contains__", name), self.__patches))


class _ConDict(dict, Configuration):  # pylint: disable=too-many-ancestors
    pass


_load_file = partial(load_file, obj_pairs_hook=Configuration)


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

    files = OrderedSet(files) if files else []

    return OrderedSet(
        chain(
            chain.from_iterable(
                map(
                    lambda a: islice(filter(os.path.isfile, starmap(os.path.join, a[1])), 1),
                    groupby(product(directories, filenames), key=lambda a: a[0]),
                )
            ),
            filter(os.path.isfile, files),
        )
    )


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
        return _get_files_from_locations(filenames=self.filenames, directories=self.directories, files=self.files)


class ConfigurationFiles(ConfigurationLocations):
    def __init__(self, files):
        super(ConfigurationFiles, self).__init__(filenames=None, directories=None, files=files)

    @classmethod
    def from_args(cls, *files):
        return cls(files)


class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames, directories):
        super(ConfigurationMultiNamedFiles, self).__init__(filenames=filenames, directories=directories, files=None)


def _get_all_unique_locations(locations):
    return OrderedSet(chain.from_iterable(map(op.methodcaller("get_locations"), locations)))


def _parse_location(location):
    if isinstance(location, ConfigurationLocations):
        return location
    elif isinstance(location, string_types):
        location = os.path.abspath(os.path.expanduser(location))
        dirname = os.path.dirname(location)
        basename, ext = os.path.splitext(os.path.basename(location))
        if ext in (".*", ".ini"):
            return ConfigurationMultiNamedFiles(
                filenames=(basename + ".yaml", basename + ".yml", basename + ".ini"), directories=(dirname,)
            )
        elif ext in (".y*", ".yml"):
            return ConfigurationMultiNamedFiles(
                filenames=(basename + ".yaml", basename + ".yml"), directories=(dirname,)
            )
        else:
            return ConfigurationFiles(files=(location,))
    else:
        raise TypeError(
            "Expected ConfigurationFiles, ConfigurationMultiNamedFiles, ConfigurationMultiNamedFiles, or a str, \
not ({})".format(
                type(location).__name__
            )
        )


class LazyLoadConfiguration(object):
    """
    Provides a lazy interface for loading Configuration from ConfigurationLocations definitions on first access.
    """

    def __init__(self, *load_order_location, **kwargs):
        base_path = kwargs.get("base_path")
        self.__base_path = base_path if base_path else []
        self._config = None
        self.__locations = tuple(map(_parse_location, load_order_location))

    def __getattr__(self, name):
        """
        Loads (if not loaded) and fetches from the underlying Configuration object.
        This also exposes the methods of Configuration.
        """
        return getattr(self.config, name)

    def load_configure(self):
        """
        Force load the configuration.
        """
        if self._config is None:
            self._config = reduce(
                lambda dic, key: dic[key],
                self.__base_path,
                _build_configuration(_get_all_unique_locations(self.__locations)),
            )
            self.__locations = None
            self.__base_path = None

    @property
    def config(self):
        """
        Loads and fetches the underlying Configuration object
        """
        if self._config is None:
            self.load_configure()
        return self._config
