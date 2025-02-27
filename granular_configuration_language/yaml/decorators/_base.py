from __future__ import annotations

import abc
import collections.abc as tabc
import dataclasses
import typing as typ
from functools import wraps

from ruamel.yaml import MappingNode, Node, SafeConstructor, ScalarNode, SequenceNode

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml.classes import RT, StateHolder, T, Tag
from granular_configuration_language.yaml.load._constructors import construct_mapping, construct_sequence

Category = typ.NewType("Category", str)
SortedAs = typ.NewType("SortedAs", str)
FriendlyType = typ.NewType("FriendlyType", str)


@dataclasses.dataclass(frozen=True, eq=False, slots=True, repr=False)
class TagConstructor:
    """
    Links the YAML Constructor to the Tag Logic
    """

    tag: Tag
    category: Category
    sort_as: SortedAs
    friendly_type: FriendlyType
    constructor: tabc.Callable[[type[SafeConstructor], StateHolder], None]
    plugin: str = dataclasses.field(default="Unknown", init=False)

    def set_plugin(self, plugin: str) -> None:
        object.__setattr__(self, "plugin", plugin)

    def __eq__(self, value: object) -> bool:
        return (isinstance(value, self.__class__) and self.tag == value.tag) or (
            isinstance(value, str) and self.tag == value
        )

    def __hash__(self) -> int:
        return hash(self.tag)

    def __call__(self, constructor: type[SafeConstructor], state: StateHolder) -> None:
        return self.constructor(constructor, state)

    def __repr__(self) -> str:
        return f"<TagConstructor(`{self.tag}`): {self.constructor.__module__}.{self.constructor.__name__}>"


class TagDecoratorBase(typ.Generic[T], abc.ABC):
    """Base class for Tag Decorator factories.

    You must implement the :py:attr:`user_friendly_type` property and define the generic type.

    Example:

    .. code-block:: python

        class string_tag(TagDecoratorBase[str]):
            Type: typing.TypeAlias = str

            @property
            def user_friendly_type(self) -> str:
                return "str"

    You must override at least one of :py:meth:`scalar_node_type_check`, :py:meth:`sequence_node_type_check`,or
    :py:meth:`mapping_node_type_check`.

    - For :py:meth:`scalar_node_type_check` to be called the YAML has already be tested to be a :py:class:`str`.
    - For :py:meth:`sequence_node_type_check` to be called the YAML has already be tested to be a
      :py:class:`~collections.abc.Sequence`.
    - For :py:meth:`mapping_node_type_check` to be called the YAML has already be tested to be a
      :py:class:`~collections.abc.Mapping`.

    If these are enough, then you may just return :py:data:`True` in the override method. Otherwise, implement the
    override as a :py:data:`~typing.TypeGuard`.

    If the value needs to be altered before being passed to Tag functions, override :py:meth:`scalar_node_transformer`,
    :py:meth:`scalar_node_transformer`, or :py:meth:`mapping_node_transformer`, as needed.

    The transformer is called if the associated node type check passes, just before the value is passed to tag function.
    """

    __slots__ = ("tag", "category", "sort_as")

    def __init__(self, tag: Tag, category: str = "General", *, sort_as: str | None = None) -> None:
        """
        :param Tag tag:
            Value of Tag.
            Expected to be constructed inline using :py:class:`.Tag` (e.g. ``Tag("!Tag")``).
            Must start with ``!``.
        :param str, optional category:
            Category of Tag. Used by :ref:`available_tags <available_tags>` and :ref:`available_plugins <available_plugins>` to organize tags, defaults to ``General``.
        :param str, optional sort_as:
            Alternative Tag string. Used for sorting tags different to its explict value. Used by :ref:`available_tags <available_tags>` and :ref:`available_plugins <available_plugins>`.
        """
        self.tag: typ.Final = tag
        self.category: typ.Final = Category(category)
        self.sort_as: typ.Final = SortedAs(sort_as or tag)

        if not tag.startswith("!"):
            raise ErrorWhileLoadingTags(f"Tag `{tag}` error: All tags must begin with `!`.")

    @property
    @abc.abstractmethod
    def user_friendly_type(self) -> str:
        """User-friendly of the type expected by Tag Decorator.

        Note:
            - Use Python types for consistent communication.
            - This is used when generating exception messages.

        :returns: User-friendly string
        :rtype: str

        """
        ...

    def scalar_node_type_check(self, value: str) -> typ.TypeGuard[T]:
        """Defaults to :py:data:`False`. Override to enable Scalar Node support.

        Parameters:
            value (str): YAML value

        Returns:
            ~typing.TypeGuard[T]: Return :py:data:`True`, if ``value`` is supported.

        """
        return False

    def sequence_node_type_check(self, value: tabc.Sequence) -> typ.TypeGuard[T]:
        """Defaults to :py:data:`False`. Override to enable Sequence Node support.

        Parameters:
            value (~collections.abc.Sequence): YAML value

        Returns:
            ~typing.TypeGuard[T]: Return :py:data:`True`, if ``value`` is supported.

        """
        return False

    def mapping_node_type_check(self, value: tabc.Mapping) -> typ.TypeGuard[T]:
        """Defaults to :py:data:`False`. Override to enable Mapping Node support.

        Parameters:
            value (~collections.abc.Mapping): YAML value

        Returns:
            ~typing.TypeGuard[T]: Return :py:data:`True`, if ``value`` is supported.

        """
        return False

    def scalar_node_transformer(self, value: typ.Any) -> T:
        """Defaults to an identity operation. Override if the value needs to be altered before being passed to Tag functions.

        Only called if :py:meth:`scalar_node_type_check` return :py:data:`True`.

        As an example, a float tag could be supported by:

        .. code-block:: python

            def scalar_node_type_check(self, value: Any) -> TypeGuard[float]:
                try:
                    float(value)
                    return True
                except ValueError:
                    return False


            def scalar_node_transformer(self, value: Any) -> float:
                return float(value)

        Parameters:
            value (~typing.Any): YAML value

        Returns:
            T: Transformed value

        """
        return value

    def sequence_node_transformer(self, value: typ.Any) -> T:
        """Defaults to an identity operation. Override if the value needs to be altered before being passed to Tag functions.

        Only called if :py:meth:`sequence_node_type_check` return :py:data:`True`.

        Parameters:
            value (~typing.Any): YAML value

        Returns:
            T: Transformed value

        """
        return value

    def mapping_node_transformer(self, value: typ.Any) -> T:
        """Defaults to an identity operation. Override if the value needs to be altered before being passed to Tag functions.

        Only called if :py:meth:`mapping_node_type_check` return :py:data:`True`.

        Parameters:
            value (~typing.Any): YAML value

        Returns:
            T: Transformed value

        """
        return value

    def __call__(self, handler: tabc.Callable[[Tag, T, StateHolder], RT]) -> TagConstructor:
        # """Takes the wrapped tag function and further wraps it for configuration loading.
        # :param (~collections.abc.Callable[[Tag, T, StateHolder], RT]) handler: Wrapped Tag Function
        # :return: Tag Function ready to be used when loading configuration
        # :rtype: TagConstructor
        # :meta private:
        # """
        # autodoc refuses to exclude `__call__`, even though this is not a part of the public interface

        # Don't capture self in the function generation
        tag = self.tag
        user_friendly_type = FriendlyType(self.user_friendly_type)
        category = self.category
        sort_as = self.sort_as
        scalar_node_type_check = self.scalar_node_type_check
        sequence_node_type_check = self.sequence_node_type_check
        mapping_node_type_check = self.mapping_node_type_check
        scalar_node_transformer = self.scalar_node_transformer
        sequence_node_transformers = self.sequence_node_transformer
        mapping_node_transformer = self.mapping_node_transformer

        @wraps(handler)
        def add_handler(
            constructor: type[SafeConstructor],
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
                    if isinstance(value, tabc.Sequence) and sequence_node_type_check(value):
                        return handler(tag, sequence_node_transformers(value), state)
                elif isinstance(node, MappingNode):
                    value = construct_mapping(state.options.obj_pairs_func, constructor, node)
                    if isinstance(value, tabc.Mapping) and mapping_node_type_check(value):
                        return handler(tag, mapping_node_transformer(value), state)
                else:
                    pass  # pragma: no cover

                # Fallback Exception
                raise ValueError(f"`{tag}` supports: {user_friendly_type}. Got: `{repr(node)}`")

            constructor.add_constructor(tag, type_handler)

        return TagConstructor(tag, category, sort_as, user_friendly_type, add_handler)
