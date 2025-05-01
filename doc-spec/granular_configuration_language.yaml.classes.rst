``granular_configuration_language`` ``.yaml.classes``
=====================================================

.. automodule:: granular_configuration_language.yaml.classes
    :members:
    :show-inheritance:
    :member-order: groupwise
    :exclude-members: P, T, RT, IT, KT, VT, Root, RootType

.. autodoc does not like Root
.. It should be a py:type, but more things breaks
.. py:class:: Root

    :py:data:`~typing.TypeAlias` used by type checking to identify the configuration root if it exists.

    alias of :py:class:`RootType` | :py:data:`None`

.. autoclass:: granular_configuration_language.yaml.classes.RootType

Internal Typing Variables
-------------------------

.. py:class:: P

    alias of ParamSpec('P')

.. autoclass:: granular_configuration_language.yaml.classes.T

.. autoclass:: granular_configuration_language.yaml.classes.RT

.. autoclass:: granular_configuration_language.yaml.classes.IT

.. py:class:: KT

    Type of the **Key** on Mappings
    
    alias of TypeVar('KT', bound= :py:class:`~collections.abc.Hashable`, default= :py:class:`~typing.Any`)

.. py:class:: VT
    
    Type of the **Value** on Mappings
    
    alias of TypeVar('VT', default= :py:class:`~typing.Any`)

.. autoclass:: granular_configuration_language._configuration.C
