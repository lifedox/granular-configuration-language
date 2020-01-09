import copy
import operator as op
import os
import typing as typ
from collections import deque
from collections.abc import Mapping, MutableMapping
from contextlib import contextmanager
from functools import partial, reduce
from itertools import chain, filterfalse, groupby, islice, product, starmap

from granular_configuration._load import load_file
from granular_configuration.exceptions import InvalidBasePathException, PlaceholderConfigurationError
from granular_configuration.utils import OrderedSet
from granular_configuration.yaml_handler import LazyEval, Placeholder

consume = partial(deque, maxlen=0)


class Patch(typ.Mapping):
    def __init__(
        self, patch_map: typ.Mapping, parent: typ.Optional["Patch"] = None, allow_new_keys: bool = False
    ) -> None:
        if not isinstance(patch_map, Mapping):
            raise TypeError("Patch expected a Mapping as input")

        self._patch = {
            key: Configuration(value) if isinstance(value, Mapping) and not isinstance(value, Configuration) else value
            for key, value in patch_map.items()
        }
        self._alive = True
        self._parent = parent
        self._allow_new_keys = allow_new_keys

    def __getitem__(self, name: typ.Any) -> typ.Any:
        return self._patch[name]

    def __iter__(self) -> typ.Iterator:
        return iter(self._patch)

    def __len__(self) -> int:
        return len(self._patch)

    def __hash__(self) -> int:
        if self._parent is not None:
            return hash(self._parent)
        else:
            return id(self)

    def __eq__(self, rhs: typ.Any) -> bool:
        return hash(self) == hash(rhs)

    @property
    def alive(self) -> bool:
        if self._parent is not None:
            return self._parent.alive
        else:
            return self._alive

    def kill(self) -> None:
        self._alive = False

    @property
    def allows_new_keys(self) -> bool:
        return self._allow_new_keys

    def make_child(self, name: str, for_patch: bool) -> "Patch":
        return self.__class__(self._patch[name], parent=self, allow_new_keys=self._allow_new_keys or for_patch)


class Configuration(typ.MutableMapping):
    def __init__(
        self, *arg: typ.Union[typ.Mapping, typ.Iterable[typ.Tuple[typ.Any, typ.Any]]], **kwargs: typ.Any
    ) -> None:
        self.__data: typ.Dict = dict()
        consume(starmap(self.__setitem__, dict(*arg, **kwargs).items()))

        self.__parent_generate_name: typ.Optional[typ.Callable[[], typ.Iterator[str]]] = None
        self.__name: typ.Optional[str] = None

        self.__patches: OrderedSet[Patch] = OrderedSet()

    def __iter__(self) -> typ.Iterator:
        if self.__has_patches():
            return iter(OrderedSet(chain(self.__data, chain.from_iterable(self.__iter_patches()))))
        else:
            return iter(self.__data)

    def __len__(self) -> int:
        if self.__has_patches():
            return len(OrderedSet(chain(self.__data, chain.from_iterable(self.__iter_patches()))))
        else:
            return len(self.__data)

    def __delitem__(self, key: typ.Any) -> None:
        return self.__data.__delitem__(key)

    def __generate_name(self, attribute: typ.Optional[str] = None) -> typ.Iterator[str]:
        if callable(self.__parent_generate_name):
            for name in self.__parent_generate_name():
                yield name
        if self.__name:
            yield self.__name
        if attribute:
            yield attribute

    def __get_name(self, attribute: typ.Optional[str] = None) -> str:
        return ".".join(self.__generate_name(attribute))

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        if isinstance(value, Configuration):
            value.__name = key
            value.__parent_generate_name = self.__generate_name
        self.__data[key] = value

    def __get_from_patches(self, name: str, default: typ.Any) -> typ.Any:
        for patch in self.__iter_patches():
            if name in patch:
                return patch[name]
        return default

    def __get_item(self, name: str) -> typ.Any:
        if self.__has_patches():
            check = object()
            patched_value = self.__get_from_patches(name, check)

            if isinstance(patched_value, Configuration):
                consume(map(patched_value.__add_patch, self.__get_child_patches(name, for_patch=True)))

            if name in self.__data:
                my_value = self.__data[name]

                if isinstance(my_value, Configuration):
                    consume(map(my_value.__add_patch, self.__get_child_patches(name, for_patch=False)))

                if isinstance(my_value, Configuration) or (patched_value is check):
                    value = my_value
                else:
                    value = patched_value
            elif (patched_value is not check) and all(map(op.attrgetter("allows_new_keys"), self.__iter_patches())):
                value = patched_value
            else:
                self.__data[name]  # raise KeyError
        else:
            value = self.__data[name]
        return value

    def __getitem__(self, name: str) -> typ.Any:
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

    def get(self, key: typ.Any, default: typ.Any = None) -> typ.Any:
        return self[key] if self.exists(key) else default

    def __getattr__(self, name: str) -> typ.Any:
        """
        Provides potentially cleaner path as an alternative to __getitem__.
        Throws AttributeError instead of KeyError, as compared to __getitem__ when an attribute is not present.
        """
        if name not in self:
            raise AttributeError('Configuration value "{}" does not exist'.format(self.__get_name(name)))

        return self[name]

    def __repr__(self) -> str:
        if self.__has_patches():
            return repr(self.as_dict())
        else:
            return repr(self.__data)

    def __contains__(self, key: typ.Any) -> bool:
        return key in self.__data or (
            self.__has_patches() and any(map(op.methodcaller("__contains__", key), self.__iter_patches()))
        )

    def exists(self, key: typ.Any) -> bool:
        """
        Checks that a key exists and is not a Placeholder
        """
        return (key in self) and not isinstance(self.__get_item(key), Placeholder)

    def as_dict(self) -> typ.Dict:
        """
        Returns the Configuration settings as standard Python dict.
        Nested Configartion object will also be converted.
        This will evaluated all lazy tag functions and throw an exception on Placeholders.
        """
        return dict(
            starmap(
                lambda key, value: (key, value.as_dict() if isinstance(value, Configuration) else value), self.items(),
            )
        )

    def __deepcopy__(self, memo: typ.Dict) -> "Configuration":
        other = Configuration()
        memo[id(self)] = other
        for key, value in self.__data.items():
            other[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return other

    def __copy__(self) -> "Configuration":
        return copy.deepcopy(self)

    copy = __copy__

    def _raw_items(self) -> typ.Iterator[typ.Tuple[typ.Any, typ.Any]]:
        return map(lambda key: (key, self.__get_item(key)), self)

    def __getnewargs__(self) -> typ.Sequence[typ.Tuple[typ.Any, typ.Any]]:
        return tuple(self.items())

    def __getstate__(self) -> typ.MutableMapping:
        return self

    def __setstate__(self, state: typ.Any) -> None:
        self.update(state)

    @property  # type: ignore
    def __class__(self):
        return _ConDict

    def __add_patch(self, patch: Patch) -> None:
        self.__patches.add(patch)

    def __has_patches(self) -> bool:
        for killed in tuple(filterfalse(op.attrgetter("alive"), self.__patches)):
            self.__patches.remove(killed)
        return bool(self.__patches)

    def __iter_patches(self) -> typ.Iterator[Patch]:
        return reversed(self.__patches)

    @contextmanager
    def patch(self, patch_map: typ.Mapping, allow_new_keys: bool = False) -> typ.Generator:
        """
        Provides a Context Manger, during whose context's values returned by this Configuration are
        replaced with the provided patch values.
        """
        patch = Patch(patch_map, allow_new_keys=allow_new_keys)
        self.__add_patch(patch)
        yield
        patch.kill()
        self.__patches.remove(patch)

    def __get_child_patches(self, name, for_patch):
        return map(
            op.methodcaller("make_child", name, for_patch),
            filter(op.methodcaller("__contains__", name), self.__patches),
        )


class _ConDict(dict, Configuration):  # type: ignore
    pass


_load_file = partial(load_file, obj_pairs_hook=Configuration)


def _build_configuration(locations: typ.Iterable[str]) -> Configuration:
    def _recursive_build_config(base_dict: Configuration, from_dict: Configuration) -> None:
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


def _get_files_from_locations(
    filenames: typ.Optional[typ.Sequence[str]] = None,
    directories: typ.Optional[typ.Sequence[str]] = None,
    files: typ.Optional[typ.Sequence[str]] = None,
) -> OrderedSet[str]:
    if not filenames or not directories:
        filenames = []
        directories = []

    if not files:
        files = []

    return OrderedSet(
        chain(
            chain.from_iterable(
                map(
                    lambda a: islice(filter(os.path.isfile, starmap(os.path.join, a[1])), 1),
                    groupby(product(directories, filenames), key=lambda a: a[0]),
                )
            ),
            filter(os.path.isfile, OrderedSet(files)),
        )
    )


class ConfigurationLocations(object):
    filenames: typ.Optional[typ.Sequence[str]]
    directories: typ.Optional[typ.Sequence[str]]
    files: typ.Optional[typ.Sequence[str]]

    def __init__(
        self,
        filenames: typ.Optional[typ.Sequence[str]] = None,
        directories: typ.Optional[typ.Sequence[str]] = None,
        files: typ.Optional[typ.Sequence[str]] = None,
    ) -> None:
        if files and (filenames or directories):
            raise ValueError("files cannot be defined with filenames and directories.")
        elif bool(filenames) ^ bool(directories):
            raise ValueError("filenames and directories are a required pair.")

        self.filenames = filenames
        self.directories = directories
        self.files = files

    def get_locations(self):
        return _get_files_from_locations(filenames=self.filenames, directories=self.directories, files=self.files)


_CLS = typ.TypeVar("_CLS", bound="ConfigurationFiles")


class ConfigurationFiles(ConfigurationLocations):
    def __init__(self, files: typ.Sequence[str]) -> None:
        super(ConfigurationFiles, self).__init__(filenames=None, directories=None, files=files)

    @classmethod
    def from_args(cls: typ.Type[_CLS], *files: str) -> _CLS:
        return cls(files)


class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames: typ.Sequence[str], directories: typ.Sequence[str]) -> None:
        super(ConfigurationMultiNamedFiles, self).__init__(filenames=filenames, directories=directories, files=None)


def _get_all_unique_locations(locations: typ.Iterable[ConfigurationLocations]) -> OrderedSet[str]:
    return OrderedSet(chain.from_iterable(map(op.methodcaller("get_locations"), locations)))


def _parse_location(location: typ.Union[str, ConfigurationLocations]) -> ConfigurationLocations:
    if isinstance(location, ConfigurationLocations):
        return location
    elif isinstance(location, str):
        location = os.path.abspath(os.path.expanduser(location))
        dirname = os.path.dirname(location)
        basename, ext = os.path.splitext(os.path.basename(location))
        if ext == ".*":
            return ConfigurationMultiNamedFiles(
                filenames=(basename + ".yaml", basename + ".yml", basename + ".ini"), directories=(dirname,)
            )
        elif ext in (".y*", ".yml"):
            return ConfigurationMultiNamedFiles(
                filenames=(basename + ".yaml", basename + ".yml"), directories=(dirname,)
            )
        elif ext == ".ini":
            return ConfigurationMultiNamedFiles(
                filenames=(basename + ".ini", basename + ".yaml", basename + ".yml"), directories=(dirname,)
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


class LazyLoadConfiguration(MutableMapping):
    """
    Provides a lazy interface for loading Configuration from ConfigurationLocations definitions on first access.
    """

    def __init__(
        self,
        *load_order_location: typ.Union[str, ConfigurationLocations],
        base_path: typ.Optional[typ.Union[str, typ.Sequence[str]]] = None,
        use_env_location: bool = False,
    ) -> None:
        self.__base_path: typ.Optional[typ.Sequence[str]]
        if isinstance(base_path, str):
            self.__base_path = [base_path]
        elif base_path:
            self.__base_path = base_path
        else:
            self.__base_path = []

        if use_env_location and ("G_CONFIG_LOCATION" in os.environ):
            env_locs = os.environ["G_CONFIG_LOCATION"].split(",")
            if env_locs:
                load_order_location = tuple(chain(load_order_location, env_locs))
        self._config: typ.Optional[Configuration] = None
        self.__locations: typ.Optional[typ.Sequence[ConfigurationLocations]] = tuple(
            map(_parse_location, load_order_location)
        )

    def __getattr__(self, name: str) -> typ.Any:
        """
        Loads (if not loaded) and fetches from the underlying Configuration object.
        This also exposes the methods of Configuration (except dunders).
        """
        return getattr(self.config, name)

    def load_configure(self) -> None:
        """
        Force load the configuration.
        """
        if self._config is None and self.__base_path is not None and self.__locations is not None:
            config = _build_configuration(_get_all_unique_locations(self.__locations))
            try:
                self._config = reduce(lambda dic, key: dic[key], self.__base_path, config)
            except KeyError as e:
                message = str(e)
                raise InvalidBasePathException(message[1 : len(message) - 1])
            self.__locations = None
            self.__base_path = None

    @property
    def config(self) -> Configuration:
        """
        Loads and fetches the underlying Configuration object
        """
        if self._config is None:
            self.load_configure()

        if self._config is None:
            raise TypeError("LazyLoadConfiguration loaded null")
        else:
            return self._config

    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    def __getitem__(self, key: typ.Any) -> None:
        return self.config[key]

    def __iter__(self) -> typ.Iterator[typ.Any]:
        return iter(self.config)

    def __len__(self) -> int:
        return len(self.config)

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value
