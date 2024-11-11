import abc
import dataclasses
import typing as typ
from functools import wraps

from ruamel.yaml import MappingNode, Node, SafeConstructor, ScalarNode, SequenceNode

from granular_configuration_language.yaml.classes import StateHolder, Tag
from granular_configuration_language.yaml.load._constructors import construct_mapping, construct_sequence

RT = typ.TypeVar("RT")
T = typ.TypeVar("T", covariant=True)


@dataclasses.dataclass(frozen=True, eq=False, slots=True, repr=False)
class TagConstructor:
    tag: Tag
    friendly_type: str
    constructor: typ.Callable[[typ.Type[SafeConstructor], StateHolder], None]

    def __eq__(self, value: object) -> bool:
        return (isinstance(value, self.__class__) and self.tag == value.tag) or (
            isinstance(value, str) and self.tag == value
        )

    def __hash__(self) -> int:
        return hash(self.tag)

    def __call__(self, constructor: typ.Type[SafeConstructor], state: StateHolder) -> None:
        return self.constructor(constructor, state)

    def __repr__(self) -> str:
        return f"<TagConstructor(`{self.tag}`): {self.constructor.__module__}.{self.constructor.__name__}>"


class TagDecoratorBase(typ.Generic[T], abc.ABC):
    """
    Base class for Tag Decorator factories.

    You must implement the `user_friendly_type` property and define the generic type.

    Example:
    ```
    class string_tag(TagDecoratorBase[str]):
        Type: typ.TypeAlias = str

        @property
        def user_friendly_type(self) -> str:
            return "str"
    ```

    You must override at least one of `scalar_node_type_check`,
    `sequence_node_type_check`,or `mapping_node_type_check`.

    - For `scalar_node_type_check` to be called the YAML has already be tested
      to be a `str`.
    - For `sequence_node_type_check` to be called the YAML has already be
      tested to be a Sequence.
    - For `mapping_node_type_check` to be called the YAML has already be tested
      to be a Mapping.

    If these are enough, then you may just return `True` in the override method.
    Otherwise, implement the override as a TypeGuard.

    If the value needs to be altered before being passed to Tag functions,
    override `scalar_node_transformer`, `scalar_node_transformer`, or
    `mapping_node_transformer`, as needed.

    The transformer call if the associated node type check passes, just before
    the value is passed to tag function.
    """

    __slots__ = ("tag",)

    def __init__(self, tag: Tag) -> None:
        self.tag: typ.Final = tag

    @property
    @abc.abstractmethod
    def user_friendly_type(self) -> str:
        """
        User friendly type version of the type expected by Tag Decorator.

        Use Python types for consistent communication.

        This is used when generating exception messages.
        """
        ...

    def scalar_node_type_check(self, value: str) -> typ.TypeGuard[T]:
        """
        Defaults to `False`. Override to enable Scalar Node support.

        Args:
            value (str): YAML value

        Returns:
            TypeGuard[T]: Return `True`, if `value` is supported.
        """
        return False

    def sequence_node_type_check(self, value: typ.Sequence) -> typ.TypeGuard[T]:
        """
        Defaults to `False`. Override to enable Sequence Node support.

        Args:
            value (Sequence): YAML value

        Returns:
            TypeGuard[T]: Return `True`, if `value` is supported.
        """
        return False

    def mapping_node_type_check(self, value: typ.Mapping) -> typ.TypeGuard[T]:
        """
        Defaults to `False`. Override to enable Mapping Node support.

        Args:
            value (Mapping): YAML value

        Returns:
            TypeGuard[T]: Return `True`, if `value` is supported.
        """
        return False

    def scalar_node_transformer(self, value: typ.Any) -> T:
        """
        Defaults to an identity operation.
        Override if the value needs to be altered before being passed
        to Tag functions.

        Only called if `scalar_node_type_check` return `True`.

        Examples:

        A float tag could be supported by:
        ```
        def scalar_node_type_check(self, value: Any) -> TypeGuard[float]:
            try:
                float(value)
                return True
            except ValueError:
                return False

        def scalar_node_transformer(self, value: Any) -> float:
            return float(value)
        ```

        Args:
            value (Any): YAML value

        Returns:
            T: Transformed value
        """
        return value

    def sequence_node_transformer(self, value: typ.Any) -> T:
        """
        Defaults to an identity operation.
        Override if the value needs to be altered before being passed
        to Tag functions.

        Only called if `sequence_node_type_check` return `True`.

        Args:
            value (Any): YAML value

        Returns:
            T: Transformed value
        """
        return value

    def mapping_node_transformer(self, value: typ.Any) -> T:
        """
        Defaults to an identity operation.
        Override if the value needs to be altered before being passed
        to Tag functions.

        Only called if `mapping_node_type_check` return `True`.

        Args:
            value (Any): YAML value

        Returns:
            T: Transformed value
        """
        return value

    def __call__(self, handler: typ.Callable[[Tag, T, StateHolder], RT]) -> TagConstructor:
        """
        Takes the wrapped tag function as wraps for configuration loading.

        Args:
            handler (Callable[[Tag, T, StateHolder], RT]): Wrapped Tag Function

        Returns:
            TagConstructor: Tag Function ready to be used when loading configuration
        """

        # Don't capture self in the function generation
        tag = self.tag
        user_friendly_type = self.user_friendly_type
        scalar_node_type_check = self.scalar_node_type_check
        sequence_node_type_check = self.sequence_node_type_check
        mapping_node_type_check = self.mapping_node_type_check
        scalar_node_transformer = self.scalar_node_transformer
        sequence_node_transformers = self.sequence_node_transformer
        mapping_node_transformer = self.mapping_node_transformer

        @wraps(handler)
        def add_handler(
            constructor: typ.Type[SafeConstructor],
            state: StateHolder,
        ) -> None:
            @wraps(handler)
            def type_handler(constructor: SafeConstructor, node: Node) -> RT:
                if isinstance(node, ScalarNode):
                    value = constructor.construct_scalar(node)
                    if isinstance(value, str) and scalar_node_type_check(value):
                        return handler(tag, scalar_node_transformer(value), state)
                elif isinstance(node, SequenceNode):
                    value = construct_sequence(state.options.sequence_func, constructor, node)
                    if isinstance(value, typ.Sequence) and sequence_node_type_check(value):
                        return handler(tag, sequence_node_transformers(value), state)
                elif isinstance(node, MappingNode):
                    value = construct_mapping(state.options.obj_pairs_func, constructor, node)
                    if isinstance(value, typ.Mapping) and mapping_node_type_check(value):
                        return handler(tag, mapping_node_transformer(value), state)
                else:
                    pass  # pragma: no cover

                # Fallback Exception
                raise ValueError(f"`{tag}` supports: {user_friendly_type}. Got: `{repr(node)}`")

            constructor.add_constructor(tag, type_handler)

        return TagConstructor(tag, user_friendly_type, add_handler)
