from __future__ import print_function

import typing as typ

from yaml import ScalarNode, MappingNode, SafeLoader


_YNODES = typ.Union[ScalarNode, MappingNode]
_RT = typ.TypeVar('_RT')
_MT = typ.TypeVar('_MT', bound=typ.Mapping)

ENV_PATTERN: typ.Pattern


class Placeholder(object):
    def __init__(self, message: str) -> None: ...


class LazyEval(object, typ.Generic[_RT]):
    def __init__(self, value: typ.Callable[[], _RT]) -> None: ...

    def run(self) -> _RT: ...


def load_env(env_name: str, default: typ.Optional[str] = None) -> str: ...


def add_cwd_to_path() -> None: ...


def get_func(func_path: str) -> typ.Callable: ...


def handle_env(loader: SafeLoader, node: _YNODES) -> LazyEval: ...


def handle_placeholder(loader: SafeLoader, node: _YNODES) -> Placeholder: ...


def handle_class(value: str) -> typ.Type[object]: ...


def handle_func(value: str) -> typ.Callable: ...


def string_check(func: typ.Callable[[str], _RT], loader: SafeLoader, node: _YNODES) -> LazyEval[_RT]: ...


def construct_mapping(cls: typ.Type[_MT], loader: SafeLoader, node: _YNODES) -> _MT: ...


def loads(yaml_str: str, obj_pairs_hook: typ.Optional[typ.Type[_MT]] = None) -> typ.Any: ...
