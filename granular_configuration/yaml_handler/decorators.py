import typing as typ
from functools import wraps

from ruamel.yaml import Node, SafeConstructor, ScalarNode, SequenceNode

from granular_configuration._yaml_classes import LazyEval, LazyEvalRootState, Root, StateHolder, StateOptions, Tag

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


def make_lazy_root(func: typ.Callable[[_T, Root], _RT]) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalRootState[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalRootState[_RT]:
        return LazyEvalRootState(tag, state.lazy_root_obj, lambda root: func(value, root))

    return lazy_wrapper


def make_lazy_root_with_state(
    func: typ.Callable[[_T, StateOptions, Root], _RT]
) -> typ.Callable[[Tag, _T, StateHolder], LazyEvalRootState[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEvalRootState[_RT]:
        options = state.options
        return LazyEvalRootState(tag, state.lazy_root_obj, lambda root: func(value, options, root))

    return lazy_wrapper


def lazy_exeception(func: typ.Callable[[_T], _RT]) -> typ.Callable[[Tag, _T, StateHolder], LazyEval[_RT]]:
    @wraps(func)
    def lazy_wrapper(tag: Tag, value: _T, state: StateHolder) -> LazyEval[_RT]:
        return func(value)  # type: ignore  # Pretend to be LazyEval, so I don't have to explicitly handle the two cases

    return lazy_wrapper


###############################################################################
# type handling decorators
###############################################################################

CallableConstructorType = typ.Callable[[typ.Type[SafeConstructor], StateHolder], None]


def string_tag(
    tag: Tag,
) -> typ.Callable[[typ.Callable[[Tag, str, StateHolder], LazyEval[_T]]], CallableConstructorType]:
    def decorator(handler: typ.Callable[[Tag, str, StateHolder], LazyEval[_T]]) -> CallableConstructorType:
        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_T]:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str):
                        return handler(tag, value, state)
                raise ValueError(f"{tag} only supports a string")

            constructor.add_constructor(tag, type_handler)

        setattr(add_handler, "_yaml_tag", tag)
        return add_handler

    return decorator


StringOrTwopleType = str | tuple[str, typ.Any]


def string_or_twople_tag(
    tag: Tag,
) -> typ.Callable[
    [typ.Callable[[Tag, StringOrTwopleType, StateHolder], LazyEval[_T]]],
    CallableConstructorType,
]:
    def decorator(
        handler: typ.Callable[[Tag, StringOrTwopleType, StateHolder], LazyEval[_T]]
    ) -> CallableConstructorType:
        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_T]:
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

        setattr(add_handler, "_yaml_tag", tag)
        return add_handler

    return decorator


SequenceOfAnyType = typ.Sequence[typ.Any]


def sequence_of_any_tag(
    tag: Tag,
) -> typ.Callable[
    [typ.Callable[[Tag, SequenceOfAnyType, StateHolder], LazyEval[_T]]],
    CallableConstructorType,
]:
    def decorator(
        handler: typ.Callable[[Tag, SequenceOfAnyType, StateHolder], LazyEval[_T]]
    ) -> CallableConstructorType:
        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_T]:
                if isinstance(node, SequenceNode):
                    value = constructor.construct_sequence(node)
                    if isinstance(value, list):
                        return handler(tag, value, state)
                raise ValueError(f"{tag} supports: list[Any]")

            constructor.add_constructor(tag, type_handler)

        setattr(add_handler, "_yaml_tag", tag)
        return add_handler

    return decorator
