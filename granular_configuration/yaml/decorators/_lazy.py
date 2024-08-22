from __future__ import annotations

import typing as typ
from functools import wraps

from granular_configuration.yaml.classes import LoadOptions, Root, StateHolder, Tag
from granular_configuration.yaml.decorators._lazy_eval import LazyEvalBasic, LazyEvalWithRoot

_RT = typ.TypeVar("_RT")
_T = typ.TypeVar("_T")


def as_lazy(func: typ.Callable[[_T], _RT]) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalBasic[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalBasic[_RT]:
        return LazyEvalBasic(tag, lambda: func(value))

    return lazy_wrapper


def as_lazy_with_load_options(
    func: typ.Callable[[_T, LoadOptions], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalBasic[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalBasic[_RT]:
        options = state.options
        return LazyEvalBasic(tag, lambda: func(value, options))

    return lazy_wrapper


def as_lazy_with_root(
    func: typ.Callable[[_T, Root], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalWithRoot[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalWithRoot[_RT]:
        return LazyEvalWithRoot(tag, state.lazy_root_obj, lambda root: func(value, root))

    return lazy_wrapper


def as_lazy_with_root_and_load_options(
    func: typ.Callable[[_T, Root, LoadOptions], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalWithRoot[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalWithRoot[_RT]:
        options = state.options
        return LazyEvalWithRoot(tag, state.lazy_root_obj, lambda root: func(value, root, options))

    return lazy_wrapper


def as_not_lazy(func: typ.Callable[[_T], _RT]) -> typ.Callable[[Tag, _T, StateHolder], _RT]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> _RT:
        return func(value)

    return lazy_wrapper
