from __future__ import annotations

import typing as typ
from functools import wraps

from granular_configuration_language.yaml.classes import LazyEval, LoadOptions, Root, StateHolder, Tag
from granular_configuration_language.yaml.decorators._lazy_eval import LazyEvalBasic, LazyEvalWithRoot
from granular_configuration_language.yaml.decorators._tag_tracker import track_as_not_lazy

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


@typ.overload
def as_lazy_with_root(
    func: typ.Callable[[_T, Root], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalWithRoot[_RT]]: ...


@typ.overload
def as_lazy_with_root(
    *, needs_root_condition: typ.Callable[[_T], bool]
) -> typ.Callable[[typ.Callable[[_T, Root], _RT]], typ.Callable[[Tag, _T, StateHolder], LazyEval[_RT]]]: ...


def as_lazy_with_root(
    func: typ.Callable[[_T, Root], _RT] | None = None, *, needs_root_condition: typ.Callable[[_T], bool] | None = None
) -> (
    typ.Callable[[Tag, _T, StateHolder], LazyEval[_RT]]
    | typ.Callable[[typ.Callable[[_T, Root], _RT]], typ.Callable[[Tag, _T, StateHolder], LazyEval[_RT]]]
):

    def decorator_generator(func: typ.Callable[[_T, Root], _RT]) -> typ.Callable[[Tag, _T, StateHolder], LazyEval[_RT]]:

        @wraps(func)
        def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEval[_RT]:

            if (needs_root_condition is None) or needs_root_condition(value):
                return LazyEvalWithRoot(tag, state.lazy_root_obj, lambda root: func(value, root))
            else:
                return LazyEvalBasic(tag, lambda: func(value, None))

        return lazy_wrapper

    if func is None:
        return decorator_generator
    else:
        return decorator_generator(func)


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

    track_as_not_lazy(func)
    return lazy_wrapper
