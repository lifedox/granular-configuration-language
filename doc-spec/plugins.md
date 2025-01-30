# Adding Custom Tags

If you need tags that are not included and have external dependencies, you add them via Python plugins (see [entry-points](https://packaging.python.org/en/latest/specifications/entry-points/#entry-points) and {py:func}`~importlib.metadata.entry_points`).

---

## Configuring you plugin library

This library using the `granular-configuration-language-20-tag` group.

### Using Poetry

Example `pyproject.toml` entry:

```toml
[tool.poetry.plugins.granular-configuration-language-20-tag]
"official_extra" = "granular_configuration_language.yaml._tags.func_and_class"
```

- `official_extra` is the name of the plugin.
  - `G_CONFIG_DISABLE_PLUGINS` uses this name.
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
def handler(value: str) -> Masked:  # Function Signature
    return Masked(getSecret(value)) # Tag Logic
```

### Function Signature

- **Name**: Completely up to you. Only used for documentation and exception messages.
- **Parameters**: At most three positional are possible (determined by your chosen [Laziness Decorator](#laziness-decorator))
  1. `value` - This is the value loaded from YAML, after its passes through the {py:class}`.TagDecoratorBase`.
     - Its type is determined by the [Tag Type Decorator](#tag-type-decorator) you use.
     - `value` will always be a single variable no matter its type or union of types. It will never be processed with `*` or `**`.
  2. {py:class}`.Root` - This is a reference to the root of final merged configuration.
     - It is used by [`!Ref`](yaml.md#ref) and [`!Sub`](yaml.md#sub) to support JSON Path and JSON Pointer querying the final configuration.
  3. {py:class}`.LoadOptions` - This a frozen {py:func}`dataclass <dataclasses.dataclass>` instance that contains the options used while loading the configuration file.
     - It is used [`!ParseFile`](yaml.md#parsefile--optionalparsefile) and [`!ParseEnv`](yaml.md#parseenv--parseenvsafe), so the delayed parsing uses the same options.
- **Return Type**: Fully controlled by you. Only used for documentation and exception messages.

### Tag Type Decorator

- Defines the Python type of the tag (`value`'s type), while naming the tag, using {py:class}`.Tag`
  - Explicitly requiring use of {py:class}`.Tag` is purely for easy `grep`-ing.
  - Tags must start with `!`
- There are four built-in options, but you can define you [own](#creating-your-own-tag-type-decorator).
  - {py:class}`.string_tag` - `str`
  - {py:class}`.string_or_twople_tag` - `str | tuple[str, typing.Any]`
  - {py:class}`.sequence_of_any_tag` - `collections.abc.Sequence[typing.Any]`
  - {py:class}`.mapping_of_any_tag` - `Configuration[typing.Any, typing.Any]`

### Laziness Decorator

- Defines the laziness of tags and the required positional parameters
  - `value`'s type is determined by [Tag Type Decorator](#tag-type-decorator).
- There are five options (these are all possible options).
  - These make the tag lazy, so the Tag Logic runs at Fetch.
    - {py:func}`.as_lazy`
      - _Positional Parameters_ - `(value: ... )`
    - {py:func}`.as_lazy_with_load_options`
      - _Positional Parameters_ - `(value: ... , options: LoadOptions)`
    - {py:func}`.as_lazy_with_root`
      - _Positional Parameters_ - `(value: ... , root: Root)`
    - {py:func}`.as_lazy_with_root_and_load_options`
      - _Positional Parameters_ - `(value: ... , root: Root, options: LoadOptions)`
  - This make the Tag Logic run at Load Time
    - {py:func}`.as_not_lazy`
      - _Positional Parameters_ - `(value: ... )`

### Interpolate Decorator

- Interpolate Decorator is **optional**. `value` must be typed as a {py:class}`str`.
- These decorators run the interpolation syntax prior to running the Tag Logic (i.e. `value` is output of the interpolation).
- Options:
  - {py:func}`.interpolate_value_without_ref` - Does not include JSON Path or JSON Pointer syntax.
  - {py:func}`.interpolate_value_with_ref` - Includes full interpolation syntax.
    - Requires {py:class}`.Root` as a parameter, even if you don't use it in the Tag Logic.

---

## Creating your own Tag Type Decorator

[Tag Type Decorators](#tag-type-decorator) are created by implementing {py:class}`.TagDecoratorBase`. See the doc-string.

[Real Examples](https://github.com/lifedox/granular-configuration-language/tree/main/granular_configuration_language/yaml/decorators/_type_checking.py)

---

## Plugin Compatibility Versioning Note

```{admonition} Notice of Future Intent
:class: note

`20` in `granular-configuration-language-20-tag` represents 2.0 tag plugin compatibility, and not directly connected to library version. Additional groups will added only if there is feature change to plugin support.

- A minor plugin change (e.g. `21`) would represent an added feature that requires a structural change but a change to the primary code.
  - Minor compatibility version deprecates any previous compatibility version (e.g. `20`).
- A major  plugin change (e.g. `30`) would represent a break change to plugin, potentially requiring complete.
  - Major compatibility version deprecates previous compatibility versions (e.g. `20` and `21`).
- A major version bump to this library may or may not introduce a new plugin compatible.
  - It would remove any deprecated versions
  - If there is no change to plugin compatibility, then only a non-zero minor would introduce to new major version.
    -  If `21` and `22` were introduced within Version 2 of this library, then Version 3 removes `20` and `21` and adds `30` as a duplicate of `22`.
    - If only `20` exists, then `30` is introduced as a duplicate of `20`, but `20` is not deprecated until a minor or major change.
  - If there is a minor plugin change, then that version becomes the next major compatibility version.
  - If there is a major plugin change, all previously supported compatibility versions are removed.
```
