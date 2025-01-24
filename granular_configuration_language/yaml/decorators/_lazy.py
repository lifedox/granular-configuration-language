from __future__ import annotations

import typing as typ
from functools import wraps

from granular_configuration_language.yaml.classes import LazyEval, LoadOptions, Root, StateHolder, Tag
from granular_configuration_language.yaml.decorators._lazy_eval import LazyEvalBasic, LazyEvalWithRoot
from granular_configuration_language.yaml.decorators._tag_tracker import track_as_not_lazy

RT = typ.TypeVar("RT")
T = typ.TypeVar("T")


def as_lazy(func: typ.Callable[[T], RT]) -> typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]:
    """Wraps the "Tag" function in a :py:class:`~.LazyEval`, so that the function being wrapped is run just-in-time.

    :param ~collections.abc.Callable[[T], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[[Tag, T, StateHolder], LazyEval[RT]]

    :note: - First Positional Argument: YAML value
    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_lazy
            def tag(value: str) -> Any:
                ...
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalBasic[RT]:
        return LazyEvalBasic(tag, lambda: func(value))

    return lazy_wrapper


def as_lazy_with_load_options(
    func: typ.Callable[[T, LoadOptions], RT]
) -> typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]:
    """Wraps the "Tag" function in a :py:class:`~.LazyEval`, so that the function being wrapped is run just-in-time.

    :param ~collections.abc.Callable[[T, LoadOptions], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[[Tag, T, StateHolder], LazyEval[RT]]

    :note: - First Positional Argument: YAML value
        - Second Positional Argument: A :py:class:`LoadOptions` instance
    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_lazy_with_load_options
            def tag(value: str, options: LoadOptions) -> Any:
                ...
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalBasic[RT]:
        options = state.options
        return LazyEvalBasic(tag, lambda: func(value, options))

    return lazy_wrapper


@typ.overload
def as_lazy_with_root(func: typ.Callable[[T, Root], RT]) -> typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]: ...


@typ.overload
def as_lazy_with_root(
    *, needs_root_condition: typ.Callable[[T], bool]
) -> typ.Callable[[typ.Callable[[T, Root], RT]], typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]]: ...


def as_lazy_with_root(
    func: typ.Callable[[T, Root], RT] | None = None, *, needs_root_condition: typ.Callable[[T], bool] | None = None
) -> (
    typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]
    | typ.Callable[[typ.Callable[[T, Root], RT]], typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]]
):
    r"""Wraps the "Tag" function in a :py:class:`~.LazyEval`, so that the function being wrapped is run just-in-time.

    Note:
        autodoc isn't exposing the :py:func:`typing.overload`. See the example for a clearer type signatures

    :param ~collections.abc.Callable[[T, Root], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[[Tag, T, StateHolder], LazyEval[RT]]

    :example:
        .. code-block:: python

            # Typical usage
            @string_tag(Tag("!Tag"))
            @as_lazy_with_root
            def tag(value: str, root: Root) -> Any:
                ...

            # Using `needs_root_condition`
            @string_tag(Tag("!Tag"))
            @as_lazy_with_root(needs_root_condition=interpolation_needs_ref_condition)
            @interpolate_value_with_ref
            def tag(value: str, root: Root) -> Any:
                ...
    """

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
) -> typ.Callable[[Tag, T, StateHolder], LazyEval[RT]]:
    """Wraps the "Tag" function in a :py:class:`~.LazyEval`, so that the function being wrapped is run just-in-time.

    :param ~collections.abc.Callable[[T, Root, LoadOptions], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[[Tag, T, StateHolder], LazyEval[RT]]

    :note: - First Positional Argument: YAML value
        - Second Positional Argument: Configuration root, as type :py:class:`Root`
        - Third Positional Argument: A :py:class:`LoadOptions` instance
    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_lazy_with_root_and_load_options
            def tag(value: str, root: Root, options: LoadOptions) -> Any:
                ...
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalWithRoot[RT]:
        options = state.options
        return LazyEvalWithRoot(tag, state.lazy_root_obj, lambda root: func(value, root, options))

    return lazy_wrapper


def as_not_lazy(func: typ.Callable[[T], RT]) -> typ.Callable[[Tag, T, StateHolder], RT]:
    """Wraps the "Tag" function, but does not make it lazy. The function being wrapped is run at load time.

    :param ~collections.abc.Callable[[T], RT] func: Function to be wrapped

    :returns: Wrapped Function
    :rtype: ~collections.abc.Callable[[Tag, T, StateHolder], LazyEval[RT]]

    :note: - First Positional Argument: YAML value
    :example:
        .. code:: python

            @string_tag(Tag("!Tag"))
            @as_not_lazy
            def tag(value: str) -> Any:
                ...
    """

    @wraps(func)
    def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> RT:
        return func(value)

    track_as_not_lazy(func)
    return lazy_wrapper
