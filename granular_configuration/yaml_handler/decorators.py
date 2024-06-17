import typing as typ

from ruamel.yaml import Node, SafeConstructor, ScalarNode, SequenceNode

from granular_configuration.yaml_handler.classes import LazyEval, LazyEvalRootState, Root, StateHolder

_RT = typ.TypeVar("_RT")
_T = typ.TypeVar("_T")


###############################################################################
# LazyEval type handling decorators
###############################################################################


def make_lazy(func: typ.Callable[[_T], _RT]) -> typ.Callable[[_T, StateHolder], LazyEval[_RT]]:
    def lazy_wrapper(value: _T, state: StateHolder) -> LazyEval[_RT]:
        return LazyEval(lambda: func(value))

    return lazy_wrapper


def make_lazy_with_state(func: typ.Callable[[_T, StateHolder], _RT]) -> typ.Callable[[_T, StateHolder], LazyEval[_RT]]:
    def lazy_wrapper(value: _T, state: StateHolder) -> LazyEval[_RT]:
        return LazyEval(lambda: func(value, state))

    return lazy_wrapper


def make_lazy_root(func: typ.Callable[[_T, Root], _RT]) -> typ.Callable[[_T, StateHolder], LazyEvalRootState[_RT]]:
    def lazy_wrapper(value: _T, state: StateHolder) -> LazyEvalRootState[_RT]:
        return LazyEvalRootState(state.lazy_root_obj, lambda root: func(value, root))

    return lazy_wrapper


def make_lazy_root_with_state(
    func: typ.Callable[[_T, StateHolder, Root], _RT]
) -> typ.Callable[[_T, StateHolder], LazyEvalRootState[_RT]]:
    def lazy_wrapper(value: _T, state: StateHolder) -> LazyEvalRootState[_RT]:
        return LazyEvalRootState(state.lazy_root_obj, lambda root: func(value, state, root))

    return lazy_wrapper


def lazy_exeception(func: typ.Callable[[_T], _RT]) -> typ.Callable[[_T, StateHolder], LazyEval[_RT]]:
    def lazy_wrapper(value: _T, state: StateHolder) -> LazyEval[_RT]:
        return func(value)  # type: ignore  # Pretend to be LazyEval, so I don't have to explicitly handle the two cases

    return lazy_wrapper


###############################################################################
# type handling decorators
###############################################################################


def string_only_tag(
    tag: str,
) -> typ.Callable[
    [typ.Callable[[str, StateHolder], LazyEval[_T]]], typ.Callable[[typ.Type[SafeConstructor], StateHolder], None]
]:
    def decorator(
        handler: typ.Callable[[str, StateHolder], LazyEval[_T]]
    ) -> typ.Callable[[typ.Type[SafeConstructor], StateHolder], None]:
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_T]:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str):
                        return handler(value, state)
                raise ValueError(f"{tag} only supports a string")

            constructor.add_constructor(tag, type_handler)

        return add_handler

    return decorator


StringOrTwopleType = str | tuple[str, typ.Any]


def string_or_twople_tag(
    tag: str,
) -> typ.Callable[
    [typ.Callable[[StringOrTwopleType, StateHolder], LazyEval[_T]]],
    typ.Callable[[typ.Type[SafeConstructor], StateHolder], None],
]:
    def decorator(
        handler: typ.Callable[[StringOrTwopleType, StateHolder], LazyEval[_T]]
    ) -> typ.Callable[[typ.Type[SafeConstructor], StateHolder], None]:
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            def type_handler(constructor: SafeConstructor, node: Node) -> LazyEval[_T]:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str):
                        return handler(value, state)
                elif isinstance(node, SequenceNode):
                    value = constructor.construct_sequence(node)
                    if isinstance(value, list) and (len(value) == 2) and isinstance(value[0], str):
                        return handler(tuple(value), state)
                raise ValueError(f"{tag} supports: str | tuple[str, Any]")

            constructor.add_constructor(tag, type_handler)

        return add_handler

    return decorator
