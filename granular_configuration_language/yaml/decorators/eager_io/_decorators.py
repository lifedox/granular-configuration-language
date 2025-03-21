from __future__ import annotations

import abc
import collections.abc as tabc
import typing as typ
from concurrent.futures import ThreadPoolExecutor

from granular_configuration_language.yaml.classes import IT, RT, LazyEval, StateHolder, T
from granular_configuration_language.yaml.decorators import LoadOptions, Root, Tag
from granular_configuration_language.yaml.decorators._lazy_eval import LazyEvalBasic, LazyEvalWithRoot
from granular_configuration_language.yaml.decorators._tag_tracker import tracker


class as_eager_io_with_root_and_load_options(abc.ABC, typ.Generic[T, RT, IT]):
    __slots__ = ("__eager_io",)

    def __init__(self, eager_io: tabc.Callable[[T, Tag, LoadOptions], IT]) -> None:
        self.__eager_io = eager_io

    def __call__(
        self,
        func: tabc.Callable[[IT, Root, LoadOptions], RT],
    ) -> tabc.Callable[[Tag, T, StateHolder], LazyEval[RT]]:
        @tracker.wraps(func, track_eager_io=self.__eager_io)
        def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalWithRoot[RT]:
            options = state.options

            eager_io_executer = ThreadPoolExecutor(1)
            eager_io_thread = eager_io_executer.submit(self.__eager_io, value, tag, options)

            def lazy_evaluator(root: Root) -> RT:
                new_value = eager_io_thread.result()
                eager_io_executer.shutdown()
                return func(new_value, root, options)

            return LazyEvalWithRoot(tag, state.lazy_root_obj, lazy_evaluator)

        return lazy_wrapper


class as_eager_io(abc.ABC, typ.Generic[T, RT, IT]):
    __slots__ = ("__eager_io",)

    def __init__(self, eager_io: tabc.Callable[[T, Tag, LoadOptions], IT]) -> None:
        self.__eager_io = eager_io

    def __call__(
        self,
        func: tabc.Callable[[IT], RT],
    ) -> tabc.Callable[[Tag, T, StateHolder], LazyEval[RT]]:
        @tracker.wraps(func, track_eager_io=self.__eager_io)
        def lazy_wrapper(tag: Tag, value: T, state: StateHolder) -> LazyEvalBasic[RT]:

            eager_io_executer = ThreadPoolExecutor(1)
            eager_io_thread = eager_io_executer.submit(self.__eager_io, value, tag, state.options)

            def lazy_evaluator() -> RT:
                new_value = eager_io_thread.result()
                eager_io_executer.shutdown()
                return func(new_value)

            return LazyEvalBasic(tag, lazy_evaluator)

        return lazy_wrapper
