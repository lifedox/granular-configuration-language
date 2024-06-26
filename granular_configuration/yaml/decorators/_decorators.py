from __future__ import annotations

import typing as typ
from functools import wraps

from ruamel.yaml import Node, SafeConstructor, ScalarNode, SequenceNode

from granular_configuration.yaml.classes import LoadOptions, Root, StateHolder, Tag
from granular_configuration.yaml.decorators._lazy_eval import LazyEvalBasic, LazyEvalWithRoot

_RT = typ.TypeVar("_RT")
_T = typ.TypeVar("_T")


###############################################################################
# LazyEval type handling decorators
###############################################################################


def as_lazy(func: typ.Callable[[_T], _RT]) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalBasic[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalBasic[_RT]:
        return LazyEvalBasic(tag, lambda: func(value))

    return lazy_wrapper


def as_lazy_with_root(
    func: typ.Callable[[_T, Root], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalWithRoot[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalWithRoot[_RT]:
        return LazyEvalWithRoot(tag, state.lazy_root_obj, lambda root: func(value, root))

    return lazy_wrapper


def as_lazy_with_root_and_load_options(
    func: typ.Callable[[_T, LoadOptions, Root], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalWithRoot[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalWithRoot[_RT]:
        options = state.options
        return LazyEvalWithRoot(tag, state.lazy_root_obj, lambda root: func(value, options, root))

    return lazy_wrapper


def as_not_lazy(func: typ.Callable[[_T], _RT]) -> typ.Callable[[Tag, _T, StateHolder], _RT]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> _RT:
        return func(value)

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
    Type: typ.TypeAlias = str

    def __call__(self, handler: typ.Callable[[Tag, Type, StateHolder], _RT]) -> CallableConstructorType:
        tag = self.tag

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> _RT:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str):
                        return handler(tag, str(value), state)
                    else:  # pragma: no cover  # untestable branch
                        # Scalar Tags are strings by definition. Checking just creates an untestable branch
                        pass
                raise ValueError(f"{tag} only supports a string. Got: `{repr(node)}`")

            constructor.add_constructor(tag, type_handler)

        return add_handler


class string_or_twople_tag(TagDecoratorBase):
    Type: typ.TypeAlias = str | tuple[str, typ.Any]

    def __call__(self, handler: typ.Callable[[Tag, Type, StateHolder], _RT]) -> CallableConstructorType:
        tag = self.tag

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> _RT:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str):
                        return handler(tag, value, state)
                    else:  # pragma: no cover  # untestable branch
                        # Scalar Tags are strings by definition. Checking just creates an untestable branch
                        pass
                elif isinstance(node, SequenceNode):
                    value = constructor.construct_sequence(node)
                    if isinstance(value, list) and (len(value) == 2) and isinstance(value[0], str):
                        return handler(tag, tuple(value), state)
                raise ValueError(f"{tag} supports: str | tuple[str, Any]. Got: `{repr(node)}`")

            constructor.add_constructor(tag, type_handler)

        return add_handler


class sequence_of_any_tag(TagDecoratorBase):
    Type: typ.TypeAlias = typ.Sequence[typ.Any]

    def __call__(self, handler: typ.Callable[[Tag, Type, StateHolder], _RT]) -> CallableConstructorType:
        tag = self.tag

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> _RT:
                if isinstance(node, SequenceNode):
                    value = constructor.construct_sequence(node)
                    if isinstance(value, list):
                        return handler(tag, value, state)
                    else:  # pragma: no cover  # untestable branch
                        # Sequence Tags are list by definition. Checking just creates an untestable branch
                        pass
                raise ValueError(f"{tag} supports: list[Any]. Got: `{repr(node)}`")

            constructor.add_constructor(tag, type_handler)

        return add_handler
