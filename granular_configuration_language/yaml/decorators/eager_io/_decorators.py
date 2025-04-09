from __future__ import annotations

import collections.abc as tabc

from granular_configuration_language._simple_future import SimpleFuture
from granular_configuration_language.yaml.classes import IT, RT, LazyEval, StateHolder, T
from granular_configuration_language.yaml.decorators import LoadOptions, Root, Tag
from granular_configuration_language.yaml.decorators._lazy_eval import LazyEvalBasic, LazyEvalWithRoot
from granular_configuration_language.yaml.decorators._tag_tracker import tracker


def as_eager_io(
    eager_io_preprocessor: tabc.Callable[[T, Tag, LoadOptions], IT],
    /,
) -> tabc.Callable[[tabc.Callable[[IT], RT]], tabc.Callable[[Tag, T, StateHolder], LazyEval[RT]]]:
    """
    .. versionadded:: 2.3.0

    .. admonition:: This an EagerIO decorator
        :class: caution
        :collapsible: closed

        **EagerIO Tags are not fully lazy.**

        The Tag logic still runs just-in-time, but the IO operations run eagerly:

        - **Load Time:** The preprocessor function runs as separate thread. This thread is spawn on load.
        - **Fetch Time:** The result of the preprocessor is then passed to tag "Tag" function instead of the YAML value.

    Wraps the "Tag" function as EagerIO tag.

    .. admonition:: Positional Parameters for "Tag" function
        :class: hint

        1. (:py:class:`~granular_configuration_language.yaml.classes.IT`) - Processor Result

    :param ~collections.abc.Callable[[T, Tag, LoadOptions] eager_io_preprocessor: EagerIO preprocessor
    :returns: Decorator Factory to wrap your "Tag" function
    :rtype: ~collections.abc.Callable[[~collections.abc.Callable[[IT], RT]], ~collections.abc.Callable[[Tag, T, StateHolder], LazyEval[RT]]]

    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_eager_io(eager_io_text_loader_interpolates)
            def tag(value: EagerIOTextFile) -> Any:
                ...
    """

    def decorator_factory(
        func: tabc.Callable[[IT], RT],
        /,
    ) -> tabc.Callable[[Tag, T, StateHolder], LazyEval[RT]]:
        @tracker.wraps(func, eager_io=eager_io_preprocessor)
        def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalBasic[RT]:
            eager_io_future = SimpleFuture(eager_io_preprocessor, value, tag, state.options)

            def lazy_evaluator() -> RT:
                return func(eager_io_future.result)

            return LazyEvalBasic(tag, lazy_evaluator)

        return lazy_wrapper

    return decorator_factory


def as_eager_io_with_root_and_load_options(
    eager_io_preprocessor: tabc.Callable[[T, Tag, LoadOptions], IT],
    /,
) -> tabc.Callable[[tabc.Callable[[IT, Root, LoadOptions], RT]], tabc.Callable[[Tag, T, StateHolder], LazyEval[RT]]]:
    """
    .. versionadded:: 2.3.0

    .. admonition:: This an EagerIO decorator
        :class: caution
        :collapsible: closed

        **EagerIO Tags are not fully lazy.**

        The Tag logic still runs just-in-time, but the IO operations run eagerly:

        - **Load Time:** The preprocessor function runs as separate thread. This thread is spawn on load.
        - **Fetch Time:** The result of the preprocessor is then passed to tag "Tag" function instead of the YAML value.

    Wraps the "Tag" function as EagerIO tag.

    .. admonition:: Positional Parameters for "Tag" function
        :class: hint

        1. (:py:class:`~granular_configuration_language.yaml.classes.IT`) - Processor Result
        2. (:py:type:`~granular_configuration_language.yaml.classes.Root`) -- Configuration root
        3. (:py:class:`.LoadOptions`) -- A :py:class:`.LoadOptions` instance


    :param ~collections.abc.Callable[[T, Tag, LoadOptions], IT] eager_io_preprocessor: EagerIO preprocessor
    :return: Decorator Factory to wrap your "Tag" function
    :rtype: ~collections.abc.Callable[[~collections.abc.Callable[[IT, Root, LoadOptions], RT]], ~collections.abc.Callable[[Tag, T, StateHolder], LazyEval[RT]]]

    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_eager_io(eager_io_text_loader_interpolates)
            def tag(value: EagerIOTextFile, root: Root, options: LoadOptions) -> Any:
                ...
    """

    def decorator_factory(
        func: tabc.Callable[[IT, Root, LoadOptions], RT],
        /,
    ) -> tabc.Callable[[Tag, T, StateHolder], LazyEval[RT]]:
        @tracker.wraps(func, eager_io=eager_io_preprocessor)
        def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalWithRoot[RT]:
            options = state.options

            eager_io_future = SimpleFuture(eager_io_preprocessor, value, tag, options)

            def lazy_evaluator(root: Root) -> RT:
                return func(eager_io_future.result, root, options)

            return LazyEvalWithRoot(tag, state.lazy_root_obj, lazy_evaluator)

        return lazy_wrapper

    return decorator_factory
