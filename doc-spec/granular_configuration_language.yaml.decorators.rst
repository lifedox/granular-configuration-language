``granular_configuration_language`` ``.yaml.decorators``
========================================================

.. autoclass:: granular_configuration_language.yaml.decorators.TagDecoratorBase
    :members:
    :show-inheritance:
    :member-order: groupwise
    :exclude-members: __call__

.. autoclass:: granular_configuration_language.yaml.decorators.mapping_of_any_tag
    :members:
    :show-inheritance:
    :member-order: groupwise
    :exclude-members: Type, __init__

    .. automethod:: __init__

    .. autodoc is not handling Type consistently

    .. py:attribute:: Type
        :type: ~typing.TypeAlias
        :value: granular_configuration_language.Configuration

        TypeAlias for this Tag factory

        alias of :py:class:`~granular_configuration_language.Configuration`

.. autoclass:: granular_configuration_language.yaml.decorators.sequence_of_any_tag
    :members:
    :show-inheritance:
    :member-order: groupwise
    :exclude-members: Type, __init__

    .. automethod:: __init__

    .. autodoc is not handling Type consistently

    .. py:attribute:: Type
        :type: ~typing.TypeAlias
        :value: typing.Sequence[typing.Any]

        TypeAlias for this Tag factory

        alias of :py:class:`~collections.abc.Sequence`\[:py:class:`~typing.Any`\]

.. autoclass:: granular_configuration_language.yaml.decorators.string_or_twople_tag
    :members:
    :show-inheritance:
    :member-order: groupwise
    :exclude-members: Type, __init__

    .. automethod:: __init__

    .. autodoc is not handling Type consistently

    .. py:attribute:: Type
        :type: ~typing.TypeAlias
        :value: str | tuple[str, typing.Any]

        TypeAlias for this Tag factory

        alias of :py:class:`str` | :py:class:`tuple`\[:py:class:`str`, :py:class:`~typing.Any`\]

.. autoclass:: granular_configuration_language.yaml.decorators.string_tag
    :members:
    :show-inheritance:
    :member-order: groupwise
    :exclude-members: Type, __init__

    .. automethod:: __init__

    .. autodoc is not handling Type consistently

    .. py:attribute:: Type
        :type: ~typing.TypeAlias
        :value: str

        TypeAlias for this Tag factory

        alias of :py:class:`str`

.. automodule:: granular_configuration_language.yaml.decorators
    :members:
    :imported-members:
    :show-inheritance:
    :member-order: groupwise
    :exclude-members: LoadOptions, Root, TagDecoratorBase, interpolate_value_with_ref, interpolate_value_without_ref, with_tag, mapping_of_any_tag, sequence_of_any_tag, string_or_twople_tag, string_tag

.. Made available from :py:mod:`.interpolate <granular_configuration_language.yaml.decorators.interpolate>`
.. --------------------------------------------------------------------------------------------------------

.. autofunction:: granular_configuration_language.yaml.decorators.interpolate_value_with_ref

.. autofunction:: granular_configuration_language.yaml.decorators.interpolate_value_without_ref

.. autofunction:: granular_configuration_language.yaml.decorators.with_tag
