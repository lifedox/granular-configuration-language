from __future__ import annotations

import collections.abc as tabc
import sys
import typing as typ
from contextlib import contextmanager
from unittest.mock import patch

from granular_configuration_language import LazyLoadConfiguration, TypedConfiguration
from granular_configuration_language._s import setter_secret
from granular_configuration_language.yaml.classes import RT, P

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: typ.Callable[P, RT]) -> typ.Callable[P, RT]:
        return func


class MutableProxy(tabc.MutableMapping):
    def __init__(self, config: TypedConfiguration) -> None:
        self.__config = config

    @override
    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.__config._private_set(key, value, setter_secret)  # noqa: SLF001

    @override
    def __delitem__(self, key: typ.Any) -> None:
        self.__config._private_del(key, setter_secret)  # noqa: SLF001

    @override
    def __iter__(self) -> tabc.Iterator:
        return iter(self.__config)

    @override
    def __len__(self) -> int:  # pragma: no cover
        return len(self.__config)

    @override
    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.__config._private_get(key, setter_secret)  # noqa: SLF001


@contextmanager
def patch_config(
    in_config: TypedConfiguration | LazyLoadConfiguration, values: tabc.Mapping[typ.Any, typ.Any], clear: bool = False
) -> tabc.Generator[None]:
    """
    Works like :py:func:`patch.dict <unittest.mock.patch.dict>` except for
    :py:class:`.Configuration` instance.

    This works around the immutability of :py:class:`.Configuration` when
    trying to use :py:func:`patch.dict <unittest.mock.patch.dict>` directly.

    .. caution::

        This is only meant to be used to mutate your configuration during your
        tests!

    :param TypedConfiguration | LazyLoadConfiguration in_config:
        :py:class:`.Configuration` being patched.
    :param ~collections.abc.Mapping[~typing.Any, ~typing.Any] values:
        dictionary of values to set in the configuration.
    :param bool clear:
        If :py:data:`True` then the configuration will be cleared before the new values are set.
    :return:
        A context manager
    :rtype: contextlib.AbstractContextManager[None]
    """
    proxy = MutableProxy(in_config.config if isinstance(in_config, LazyLoadConfiguration) else in_config)

    with patch.dict(proxy, values, clear):
        yield
