# Adding Custom Tags

If you need tags that are not included and have external dependencies, you add them via Python plugins (see [entry-points](https://packaging.python.org/en/latest/specifications/entry-points/#entry-points) and {py:func}`~importlib.metadata.entry_points`).

---

## Configuring you plugin library

This library using the `granular_configuration_language_20_tag` group.

### Using `pyproject.toml`

Example `pyproject.toml` entry:

```toml
[project.entry-points."granular_configuration_language_20_tag"]
"official_extra" = "granular_configuration_language.yaml._tags.func_and_class"
```

- `official_extra` is the name of the plugin.
  - [`G_CONFIG_DISABLE_PLUGINS`](configuration.md#environment-variables) uses this name.
  - No whitespace in names.
- `granular_configuration_language.yaml._tags.func_and_class` is the module searched for Tags.
  - Please keep this import lightweight.

---

## Writing your own tag

[Real Examples](https://github.com/lifedox/granular-configuration-language/tree/main/granular_configuration_language/yaml/_tags)

To make adding tags easy, the logic has been wrapped into a series of ordered decorators, leaving you three choices to make.

Everything you need is importable from {py:mod}`granular_configuration_language.yaml.decorators`.

### Example

```python
from credstash import getSecret
from granular_configuration_language.yaml.classes import Masked
from granular_configuration_language.yaml.decorators import (
    Tag, as_lazy, interpolate_value_without_ref, string_tag
)


@string_tag(Tag("!Credstash"))      # Tag Type Decorator
@as_lazy                            # Laziness Decorator
@interpolate_value_without_ref      # (Optional) Interpolate Decorator
# @with_tag                         # (Optional) With Attribute Decorator
def handler(value: str) -> Masked:  # Function Signature
    return Masked(getSecret(value)) # Tag Logic
```

<br>

### Function Signature

- **Name**: Completely up to you. Only used for documentation and exception messages.
- **Parameters**: At most three positional are possible (determined by your chosen [Laziness Decorator](#laziness-decorator)).
  1. `value` - This is the value loaded from YAML, after its passes through the {py:class}`.TagDecoratorBase`.
     - Its type is determined by the [Tag Type Decorator](#tag-type-decorator) you use.
     - `value` will always be a single variable no matter its type or union of types. It will never be processed with `*` or `**`.
  2. {py:class}`.Root` - This is a reference to the root of final merged configuration.
     - It is used by [`!Ref`](yaml.md#ref) and [`!Sub`](yaml.md#sub) to support JSON Path and JSON Pointer querying the final configuration.
  3. {py:class}`.LoadOptions` - This a frozen {py:func}`dataclass <dataclasses.dataclass>` instance that contains the options used while loading the configuration file.
     - It is used [`!ParseFile`](yaml.md#parsefile--optionalparsefile) and [`!ParseEnv`](yaml.md#parseenv--parseenvsafe), so the delayed parsing uses the same options.
- **Return Type**: Fully controlled by you. Only used for documentation and exception messages.

### Tag Type Decorator

- Defines the Python type of the tag (`value`'s type), while naming the tag, using {py:class}`.Tag`.
  - Explicitly requiring use of {py:class}`.Tag` is purely for easy `grep`-ing.
  - Tags must start with `!`.
- There are four built-in options, but you can define you [own](#creating-your-own-tag-type-decorator).
  - {py:class}`.string_tag` - `str`
  - {py:class}`.string_or_twople_tag` - `str | tuple[str, typing.Any]`
  - {py:class}`.sequence_of_any_tag` - `collections.abc.Sequence[typing.Any]`
  - {py:class}`.mapping_of_any_tag` - `Configuration[typing.Any, typing.Any]`

### Laziness Decorator

- Defines the laziness of tags and the required positional parameters.
  - `value`'s type is determined by [Tag Type Decorator](#tag-type-decorator).
- There are five options (these are all the possible options).
  - These make the tag lazy, so the Tag Logic runs at Fetch.
    - {py:func}`.as_lazy`
      - _Positional Parameters_ - `(value: ... )`
    - {py:func}`.as_lazy_with_load_options`
      - _Positional Parameters_ - `(value: ... , options: LoadOptions)`
    - {py:func}`.as_lazy_with_root`
      - _Positional Parameters_ - `(value: ... , root: Root)`
      - Note: {py:func}`.as_lazy_with_root` has a decorator factory version.
        - Keyword Parameters:
          - `needs_root_condition`: `Callable[[ ... ], bool]`
        - Used by [`!Sub`](yaml.md#sub) to check if Root is required before holding on to a reference to it.
    - {py:func}`.as_lazy_with_root_and_load_options`
      - _Positional Parameters_ - `(value: ... , root: Root, options: LoadOptions)`
  - This make the Tag Logic run at Load Time
    - {py:func}`.as_not_lazy`
      - _Positional Parameters_ - `(value: ... )`

### Interpolate Decorator

- Interpolate Decorator is **optional**. `value` must be a {py:class}`str`.
- These decorators run the interpolation syntax prior to running the Tag Logic (i.e. `value` is output of the interpolation).
- Options:
  - {py:func}`.interpolate_value_without_ref` - Does not include JSON Path or JSON Pointer syntax.
  - {py:func}`.interpolate_value_with_ref` - Includes full interpolation syntax.
    - Requires {py:class}`.Root` as the second parameter, even if you don't use it in the Tag Logic.

### With Attribute Decorator

- Currently, only {py:func}`.with_tag` is available, if you need your tag.
- With the {py:func}`.with_tag` decorator, a {py:class}`.Tag` parameter is prepended before the `value` parameter.
  - The {py:func}`.with_tag` decorator removes the {py:class}`.Tag` parameter from the function signature, so that it invisibly works with the functionality decorators.

**Example:**

```python
from credstash import getSecret
from granular_configuration_language.yaml.classes import Masked
from granular_configuration_language.yaml.decorators import (
    Tag, as_lazy, interpolate_value_without_ref, string_tag, with_tag
)


@string_tag(Tag("!Credstash"))      # Tag Type Decorator
@as_lazy                            # Laziness Decorator
@interpolate_value_without_ref      # (Optional) Interpolate Decorator
@with_tag
def handler(tag: Tag, value: str) -> Masked:  # Function Signature
    return Masked(getSecret(value)) # Tag Logic
```

---

## Creating your own Tag Type Decorator

[Tag Type Decorators](#tag-type-decorator) are created by implementing {py:class}`.TagDecoratorBase`.

[Real Examples](https://github.com/lifedox/granular-configuration-language/tree/main/granular_configuration_language/yaml/decorators/_type_checking.py)

### Defining the Type of your Tag Type Decorator

```python
import typing
from granular_configuration_language.yaml.decorators import (
    TagDecoratorBase,
)

class float_tag(TagDecoratorBase[float]):
    Type: typing.TypeAlias = float

    @property
    def user_friendly_type(self) -> str:
        return "float"
```

<br>

The required portion of {py:class}`.TagDecoratorBase` is to set the Python type a Tag takes as input. You set it in the {py:class}`~typing.Generic` argument, and you implement the {py:meth}`~.TagDecoratorBase.user_friendly_type` property. The property is expected to match Generic argument, but to be as straightforward as possible. For example, {py:class}`.sequence_of_any_tag` uses `collections.abc.Sequence[typing.Any]` as Generic argument, but property just returns `list[Any]`.

The {py:data}`~typing.TypeAlias`, `Type`, is just a nicety for users of your Tag Type Decorator. Case in point, `str | tuple[str, typing.Any]]` is more effort to type than `string_or_twople_tag.Type`.

:::{admonition} Implementation Excuse
:class: note
:collapsible: closed

While it is possible to implement {py:meth}`~.TagDecoratorBase.user_friendly_type` in the {py:class}`.TagDecoratorBase`. The properties required are not defined in PyRight, and it needs a lot of checks and special case handling, especially since I don't want `collections.abc.` or `typing.`

The guaranteed to never break and handling all possible cases solution is the author of the Tag Type Decorator just writing what they think is best.
:::

### Configuring your Tag Type Decorator

```python
class float_tag(TagDecoratorBase[float]):

    # ...

    @typing.override  # Python 3.12+
    def scalar_node_type_check(
        self,
        value: str,
    ) -> typing.TypeGuard[float]:
        """"""  # Make undocumented

        # As of Version 2.3.0, a `ValueError` raised
        # during `type_check` or `transformers` will
        # be converted into a properly messaged
        # `TagHadUnsupportArgument`, so this method
        # could just be `return True`.

        try:
            float(value)
            return True
        except ValueError:
            return False

    @typing.override  # Python 3.12+
    def scalar_node_transformer(
        self,
        value: typing.Any,
    ) -> float:
        """"""  # Make undocumented
        return float(value)
```

<br>

YAML Tags support Scalar, Sequence, and Mapping YAML types. These are {py:class}`str`, {py:class}`~collections.abc.Sequence`, and {py:class}`~collections.abc.Mapping` in Python.

For each YAML type, there is an associated `type_check` method. These methods are called after the YAML type is checked. Use these to narrow the type of your Tag Type Decorator.

- {py:meth}`~.TagDecoratorBase.scalar_node_type_check`
  - Called if the type of `value` is {py:class}`str`.
  - Default return is {py:data}`False`.
  - Return type is {py:data}`TypeGuard[T] <typing.TypeGuard>`, which is a {py:class}`bool` value.
- {py:meth}`~.TagDecoratorBase.sequence_node_type_check`
  - Called if the type of `value` is `collections.abc.Sequence[typing.Any]`.
  - Default return is {py:data}`False`.
  - Return type is {py:data}`TypeGuard[T] <typing.TypeGuard>`, which is a {py:class}`bool` value.
- {py:meth}`~.TagDecoratorBase.mapping_node_type_check`
  - Called if the type of `value` is `collections.abc.Mapping[typing.Any, typing.Any]`.
  - Default return is {py:data}`False`.
  - Return type is {py:data}`TypeGuard[T] <typing.TypeGuard>`, which is a {py:class}`bool` value.

If you need to mutate `value` from a YAML type to a different Python type, there are `transformer` methods. These methods are called after the `type_check` method.

- {py:meth}`~.TagDecoratorBase.scalar_node_transformer`
  - Called if the type of `value` is {py:class}`str`.
  - Default return is `value` (identity operation).
  - Return type is {py:class}`~.T`
- {py:meth}`~.TagDecoratorBase.sequence_node_transformer`
  - Called if the type of `value` is `collections.abc.Sequence[typing.Any]`.
  - Default return is `value` (identity operation).
  - Return type is {py:class}`~.T`
- {py:meth}`~.TagDecoratorBase.mapping_node_transformer`
  - Called if the type of `value` is `collections.abc.Mapping[typing.Any, typing.Any]`.
  - Default return is `value` (identity operation).
  - Return type is {py:class}`~.T`

:::{tip}

If you generate documentation, it is recommended to override the doc-string with an empty string when you override a `type_check` or `transformer`, as these methods are implementation detail, not public interface.

:::

---

## Plugin Compatibility Versioning Note

:::{admonition} Notice of Future Intent
:class: note

`20` in `granular_configuration_language_20_tag` represents 2.0 tag plugin compatibility, and not directly connected to library version. Additional groups will be added only if there is feature change to plugin support.

- A minor plugin change (e.g. `21`) would represent an added feature that requires a structural change but not a change to the primary code.
  - A minor compatibility version bump deprecates any previous compatibility version (e.g. `20`).
    - Both `20` and `21` would be supported, with `20` deprecated, using a compatibility layer.
- A major plugin change (e.g. `30`) would represent a breaking change to plugin, potentially requiring a complete code change.
  - A major compatibility version bump deprecates all previous compatibility versions (e.g. `20` and `21`).
    - If the library does not major version, then `20`, `21`, `30` would be all be supported, with `20` and `21` deprecated, using compatibility layers.
- A major version bump to this library may or may not introduce a new plugin compatible.
  - It would remove any deprecated versions.
  - If there is no change to plugin compatibility, then only a non-zero minor plugin version would introduce to new major plugin version.
    - If `21` and `22` were introduced within Version 2 of this library, then Version 3 removes `20` and `21`, keeps `22`, and adds `30` as a duplicate of `22`. Version 4 would remove `22`, keep `30`, and add `40` as duplicate of `30`
    - If only `20` exists, then `30` is introduced as a duplicate of `20`, but `20` is not deprecated until a minor or major change.
      - Adding `x0` for every non-breaking major version `x` is to reduce developer overhead. "Just match the major version of the minimum of your supported dependency range."
  - If there is a minor plugin change, then that version becomes the next major compatibility version.
  - If there is a major plugin change, all previously supported compatibility versions are removed.

:::
