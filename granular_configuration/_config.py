import copy
import typing as typ
from itertools import chain, starmap

from granular_configuration._utils import consume
from granular_configuration.exceptions import PlaceholderConfigurationError
from granular_configuration.yaml import LazyEval, Placeholder


class Configuration(typ.MutableMapping):
    def __init__(self, *arg: typ.Mapping | typ.Iterable[typ.Tuple[typ.Any, typ.Any]], **kwargs: typ.Any) -> None:
        self.__data: typ.Dict = dict()
        self.__names: typ.Tuple[str, ...] = tuple()

        consume(starmap(self.__setitem__, dict(*arg, **kwargs).items()))

    def __iter__(self) -> typ.Iterator:
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)

    def __delitem__(self, key: typ.Any) -> None:
        return self.__data.__delitem__(key)

    def __get_name(self, attribute: typ.Any) -> str:
        return ".".join(map(str, chain(self.__names, (str(attribute),))))

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.__data[key] = value

    def __getitem__(self, name: typ.Any) -> typ.Any:
        try:
            value = self.__data[name]
        except KeyError:
            # Start the stack trace here
            raise KeyError(repr(name)) from None

        if isinstance(value, Placeholder):
            raise PlaceholderConfigurationError(
                f'Configuration expects "{self.__get_name(name)}" to be overwritten. Message: "{value}"'
            )
        elif isinstance(value, LazyEval):
            try:
                new_value = value.result
                self[name] = new_value
                return new_value
            except RecursionError:
                raise RecursionError(
                    f"{value.tag} at `{self.__get_name(name)}` caused a recursion error. Please check your configuration for a self-referencing loop."
                ) from None
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
            raise AttributeError(f'Configuration value "{self.__get_name(name)}" does not exist')

        return self[name]

    def __repr__(self) -> str:  # pragma: no cover
        return repr(self.__data)

    def __contains__(self, key: typ.Any) -> bool:
        return key in self.__data

    def exists(self, key: typ.Any) -> bool:
        """
        Checks that a key exists and is not a Placeholder
        """
        return (key in self) and not isinstance(self.__data[key], Placeholder)

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
        return map(lambda key: (key, self.__data[key]), self)

    def __getnewargs__(self) -> typ.Sequence[typ.Tuple[typ.Any, typ.Any]]:  # pragma: no cover
        return tuple(self.items())

    def __getstate__(self) -> typ.MutableMapping:  # pragma: no cover
        return self

    def __setstate__(self, state: typ.Any) -> None:  # pragma: no cover
        self.update(state)

    @property  # type: ignore
    def __class__(self):  # type: ignore
        return _ConDict


class _ConDict(dict, Configuration):  # type: ignore
    pass
