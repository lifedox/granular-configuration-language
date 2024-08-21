import abc
import typing as typ
from functools import wraps

from ruamel.yaml import Node, SafeConstructor, ScalarNode, SequenceNode

from granular_configuration.yaml.classes import StateHolder, Tag

_RT = typ.TypeVar("_RT")
_T = typ.TypeVar("_T")


class TagConstructor():
    __slots__ = ("tag", "constructor")

    def __init__(self, tag: Tag, constructor: typ.Callable[[typ.Type[SafeConstructor], StateHolder], None]) -> None:
        self.tag: typ.Final = tag
        self.constructor: typ.Final = constructor

    def __eq__(self, value: object) -> bool:  # pragma: no cover
        return (isinstance(value, self.__class__) and self.tag == value.tag) or (
            isinstance(value, str) and self.tag == value
        )

    def __call__(self, constructor: typ.Type[SafeConstructor], state: StateHolder) -> None:
        return self.constructor(constructor, state)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TagConstructor(`{self.tag}`): {self.constructor.__module__}.{self.constructor.__name__}>"


class TagDecoratorBase(typ.Generic[_T], abc.ABC):
    __slots__ = ("tag",)

    def __init__(self, tag: Tag) -> None:
        self.tag: typ.Final = tag

    @property
    @abc.abstractmethod
    def user_friendly_type(self) -> str: ...  # pragma: no cover

    def scalar_node_type_check(self, value: str) -> typ.TypeGuard[_T]:
        return False

    def sequence_node_type_check(self, value: typ.MutableSequence) -> typ.TypeGuard[_T]:
        return False

    def scalar_node_transformer(self, value: typ.Any) -> _T:
        return value

    def sequence_node_transformer(self, value: typ.Any) -> _T:
        return value

    def __call__(self, handler: typ.Callable[[Tag, _T, StateHolder], _RT]) -> TagConstructor:
        # Don't capture self in the function generation
        tag = self.tag
        user_friendly_type = self.user_friendly_type
        scalar_node_type_check = self.scalar_node_type_check
        sequence_node_type_check = self.sequence_node_type_check
        scalar_node_transformer = self.scalar_node_transformer
        sequence_node_transformers = self.sequence_node_transformer

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> _RT:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str) and scalar_node_type_check(value):
                        return handler(tag, scalar_node_transformer(value), state)
                elif isinstance(node, SequenceNode):
                    value = constructor.construct_sequence(node)
                    if isinstance(value, typ.MutableSequence) and sequence_node_type_check(value):
                        return handler(tag, sequence_node_transformers(value), state)

                # Fallback Exception
                raise ValueError(f"{tag} supports: {user_friendly_type}. Got: `{repr(node)}`")

            constructor.add_constructor(tag, type_handler)

        return TagConstructor(tag, add_handler)
