from __future__ import annotations

import typing as typ
from functools import wraps

from ruamel.yaml import Node, SafeConstructor, ScalarNode, SequenceNode

from granular_configuration.yaml.classes import LazyEval, LazyEvalRootState, LoadOptions, Root, StateHolder, Tag

_RT = typ.TypeVar("_RT")
_T = typ.TypeVar("_T")


###############################################################################
# LazyEval type handling decorators
###############################################################################


def make_lazy(func: typ.Callable[[_T], _RT]) -> typ.Callable[[Tag, _T, StateHolder], LazyEval[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEval[_RT]:
        return LazyEval(tag, lambda: func(value))

    return lazy_wrapper


def make_lazy_with_root(
    func: typ.Callable[[_T, Root], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalRootState[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalRootState[_RT]:
        return LazyEvalRootState(tag, state.lazy_root_obj, lambda root: func(value, root))

    return lazy_wrapper


def make_lazy_with_root_and_load_options(
    func: typ.Callable[[_T, LoadOptions, Root], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalRootState[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalRootState[_RT]:
        options = state.options
        return LazyEvalRootState(tag, state.lazy_root_obj, lambda root: func(value, options, root))

    return lazy_wrapper


def make_lazy_exeception(func: typ.Callable[[_T], _RT]) -> typ.Callable[[Tag, _T, StateHolder], LazyEval[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEval[_RT]:
        return func(value)  # type: ignore  # Pretend to be LazyEval, so I don't have to explicitly handle the two cases

    return lazy_wrapper


###############################################################################
# type handling decorators
###############################################################################

CallableConstructorType = typ.Callable[[typ.Type[SafeConstructor], StateHolder], None]


class TagDecoratorBase:
    __slots__ = ("tag",)

    def __init__(self, tag: Tag) -> None:
        self.tag: typ.Final = tag


class string_tag(TagDecoratorBase):
    Type = str

    def __call__(self, handler: typ.Callable[[Tag, Type, StateHolder], LazyEval[_RT]]) -> CallableConstructorType:
        tag = self.tag

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_RT]:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str):
                        return handler(tag, value, state)
                raise ValueError(f"{tag} only supports a string")

            constructor.add_constructor(tag, type_handler)

        return add_handler


class string_or_twople_tag(TagDecoratorBase):
    Type = str | tuple[str, typ.Any]

    def __call__(self, handler: typ.Callable[[Tag, Type, StateHolder], LazyEval[_RT]]) -> CallableConstructorType:
        tag = self.tag

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_RT]:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str):
                        return handler(tag, value, state)
                elif isinstance(node, SequenceNode):
                    value = constructor.construct_sequence(node)
                    if isinstance(value, list) and (len(value) == 2) and isinstance(value[0], str):
                        return handler(tag, tuple(value), state)
                raise ValueError(f"{tag} supports: str | tuple[str, Any]")

            constructor.add_constructor(tag, type_handler)

        return add_handler


class sequence_of_any_tag(TagDecoratorBase):
    Type = typ.Sequence[typ.Any]

    def __call__(self, handler: typ.Callable[[Tag, Type, StateHolder], LazyEval[_RT]]) -> CallableConstructorType:
        tag = self.tag

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_RT]:
                if isinstance(node, SequenceNode):
                    value = constructor.construct_sequence(node)
                    if isinstance(value, list):
                        return handler(tag, value, state)
                raise ValueError(f"{tag} supports: list[Any]")

            constructor.add_constructor(tag, type_handler)

        return add_handler