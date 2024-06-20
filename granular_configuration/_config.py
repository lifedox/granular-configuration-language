import copy
import operator as op
import typing as typ
from collections.abc import Mapping
from contextlib import contextmanager
from itertools import chain, filterfalse, starmap

from granular_configuration._yaml_classes import LazyEval, Placeholder
from granular_configuration.exceptions import PlaceholderConfigurationError
from granular_configuration.utils import OrderedSet, consume


class Patch(typ.Mapping):
    def __init__(
        self, patch_map: typ.Mapping, parent: typ.Optional["Patch"] = None, allow_new_keys: bool = False
    ) -> None:
        if not isinstance(patch_map, Mapping):  # pragma: no cover
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

    def __len__(self) -> int:  # pragma: no cover
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
        self.__names: typ.Tuple[str, ...] = tuple()
        self.__patches: OrderedSet[Patch] = OrderedSet()

        consume(starmap(self.__setitem__, dict(*arg, **kwargs).items()))

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

    def __get_name(self, attribute: typ.Any) -> str:
        return ".".join(map(str, chain(self.__names, (str(attribute),))))

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.__data[key] = value

    def __get_from_patches(self, name: str, default: typ.Any) -> typ.Any:
        for patch in self.__iter_patches():
            if name in patch:
                return patch[name]
        return default

    def __get_item(self, name: typ.Any) -> typ.Any:
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
                raise KeyError(str(name))  # pragma: no cover
        else:
            value = self.__data[name]
        return value

    def __getitem__(self, name: typ.Any) -> typ.Any:
        try:
            value = self.__get_item(name)
        except KeyError:
            # Start the stack trace here
            raise KeyError(repr(name)) from None

        if isinstance(value, Placeholder):
            raise PlaceholderConfigurationError(
                'Configuration expects "{}" to be overwritten. Message: "{}"'.format(self.__get_name(name), value)
            )
        elif isinstance(value, LazyEval):
            new_value = value.run()
            while isinstance(new_value, LazyEval):
                new_value = new_value.run()
            self[name] = new_value
            return new_value
        elif isinstance(value, Configuration):
            value.__names = self.__names + (str(name),)
            return value
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

    def __repr__(self) -> str:  # pragma: no cover
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
                lambda key, value: (key, value.as_dict() if isinstance(value, Configuration) else value),
                self.items(),
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

    def __getnewargs__(self) -> typ.Sequence[typ.Tuple[typ.Any, typ.Any]]:  # pragma: no cover
        return tuple(self.items())

    def __getstate__(self) -> typ.MutableMapping:  # pragma: no cover
        return self

    def __setstate__(self, state: typ.Any) -> None:  # pragma: no cover
        self.update(state)

    @property  # type: ignore
    def __class__(self):  # type: ignore
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

    def __get_child_patches(self, name: str, for_patch: bool) -> typ.Iterator[Patch]:
        return map(
            op.methodcaller("make_child", name, for_patch),
            filter(op.methodcaller("__contains__", name), self.__patches),
        )


class _ConDict(dict, Configuration):  # type: ignore
    pass
