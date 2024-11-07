from __future__ import annotations

import typing as typ
from functools import wraps

from granular_configuration_language.yaml.classes import LazyEval, LoadOptions, Root, StateHolder, Tag
from granular_configuration_language.yaml.decorators._lazy_eval import LazyEvalBasic, LazyEvalWithRoot
from granular_configuration_language.yaml.decorators._tag_tracker import track_as_not_lazy

RT = typ.TypeVar("RT")
T = typ.TypeVar("T")


def as_lazy(func: typ.Callable[[T], RT]) -> typ.Callable[[Tag, T, StateHolder], LazyEvalBasic[RT]]:
    """
    Wraps the "Tag" function in a `LazyEval`, so that the function being wrapped is run just-in-time.

    Only the YAML value is provided to the function being wrapped.

    Args:
        func (Callable[[T], RT]): Function being wrapped

    Returns:
        Callable[[Tag, T, StateHolder], LazyEvalBasic[RT]]: Wrapped function
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalBasic[RT]:
        return LazyEvalBasic(tag, lambda: func(value))

    return lazy_wrapper


def as_lazy_with_load_options(
    func: typ.Callable[[T, LoadOptions], RT]
) -> typ.Callable[[Tag, T, StateHolder], LazyEvalBasic[RT]]:
    """
    Wraps the "Tag" function in a `LazyEval`, so that the function being wrapped is run just-in-time.

    - The YAML value is provided to the function being wrapped as the first positional argument.
    - A `LoadOptions` instance is provided as the second positional argument.

    Args:
        func (Callable[[T, LoadOptions], RT]): Function being wrapped

    Returns:
        (Callable[[Tag, T, StateHolder], LazyEvalBasic[RT]]): Wrapped function
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalBasic[RT]:
        options = state.options
        return LazyEvalBasic(tag, lambda: func(value, options))

    return lazy_wrapper


@typ.overload
def as_lazy_with_root(func: typ.Callable[[T, Root], RT]) -> typ.Callable[[Tag, T, StateHolder], LazyEvalWithRoot[RT]]:
    """
    Wraps the "Tag" function in a `LazyEval`, so that the function being wrapped is run just-in-time.

    - The YAML value is provided to the function being wrapped as the first positional argument.
    - The Configuration root is provided as the second positional argument.

    Args:
        func (Callable[[T, Root], RT]): Function being wrapped

    Returns:
        (Callable[[Tag, T, StateHolder], LazyEvalWithRoot[RT]]): Wrapped function
    """
    ...


@typ.overload
def as_lazy_with_root(
    *, needs_root_condition: typ.Callable[[T], bool]
) -> typ.Callable[[typ.Callable[[T, Root], RT]], typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]]:
    r"""
    Wraps the "Tag" function in a `LazyEval`, so that the function being wrapped is run just-in-time.

    - The YAML value is provided to the function being wrapped as the first positional argument.
    - The Configuration root is provided as the second positional argument.

    In this mode, this function a decorator factory.

    Args:
        needs_root_condition (Callable[[T], bool]): Function used to test if the Configuration Root is needed.
                                                    This function is provided the YAML value.
                                                    When False, the second positional argument is always None.

    Returns:
        (Callable[[Callable[[T, Root], RT]], Callable[\[Tag, T, StateHolder], LazyEval[RT]]]): Decorator
    """
    ...


def as_lazy_with_root(
    func: typ.Callable[[T, Root], RT] | None = None, *, needs_root_condition: typ.Callable[[T], bool] | None = None
) -> (
    typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]
    | typ.Callable[[typ.Callable[[T, Root], RT]], typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]]
):

    def decorator_generator(func: typ.Callable[[T, Root], RT]) -> typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]:

        @wraps(func)
        def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEval[RT]:

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
    func: typ.Callable[[T, Root, LoadOptions], RT]
) -> typ.Callable[[Tag, T, StateHolder], LazyEvalWithRoot[RT]]:
    """
    Wraps the "Tag" function in a `LazyEval`, so that the function being wrapped is run just-in-time.

    - The YAML value is provided to the function being wrapped as the first positional argument.
    - The Configuration root is provided as the second positional argument.
    - A `LoadOptions` instance is provided as the third positional argument.

    Args:
        func (Callable[[T, Root, LoadOptions], RT]): Function being wrapped

    Returns:
        (Callable[[Tag, T, StateHolder], LazyEvalWithRoot[RT]]): Wrapped function
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalWithRoot[RT]:
        options = state.options
        return LazyEvalWithRoot(tag, state.lazy_root_obj, lambda root: func(value, root, options))

    return lazy_wrapper


def as_not_lazy(func: typ.Callable[[T], RT]) -> typ.Callable[[Tag, T, StateHolder], RT]:
    """
    Wraps the "Tag" function, but does not make it lazy. The function being wrapped is run at load time.

    Args:
        func (Callable[[T], RT]): Function being wrapped

    Returns:
        (Callable[[Tag, T, StateHolder], RT]): Wrapped function
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> RT:
        return func(value)

    track_as_not_lazy(func)
    return lazy_wrapper
