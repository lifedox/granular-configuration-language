# Getting Started

## Defining a Configuration

Configuration is always defined by constructing a {py:class}`.LazyLoadConfiguration` and providing the paths to possible files. Paths can be {py:class}`str` or {py:class}`pathlib.Path` objects.

Examples:

### One-off library with three possible sources

```python
from granular_configuration_language import Configuration, LazyLoadConfiguration

CONFIG = LazyLoadConfiguration(
    Path(__file___).parent / "config.yaml",
    "~/.config/really_cool_library_config.yaml",
    "./really_cool_library_config.yaml",
)
```

- Comments:
  - `Path(__file___).parent /` creates a file relative directory. Using this ensures that the embedded configuration (the one shipped with this library) is correctly reference within site-package.
    - This example shows the common pattern of having a `config.py` (or `config` with `_config.py`) and then have config file (`config.yaml`) live next to it.
    - ⚠️ Don't forget to add the embedded config to package data.
  - `~/.config/` is useful when you have settings that developers may want to on their machines.
    - For example, plain text logs while debugging and JSON logs for deploys.
  - `./` is useful for application deployment-specific settings.
    - For example, say we have an application deploying to a Lambda package and a container service. With a current working directory option, Lambda specific settings and the container specific settings are single file addition to common deploy package.

### Library that shares configuration files with other libraries

```python
from granular_configuration_language import Configuration, LazyLoadConfiguration

CONFIG = LazyLoadConfiguration(
    Path(__file___).parent / "config.yaml",
    "~/.config/really_cool_library_config.yaml",
    "./really_cool_library_config.yaml",
    "~/.config/common_framework_config.yaml",
    "./common_framework_config.yaml",
    base_path="really_cool_library",
)
```

- Comments:
  - Ecosystem/framework for configuration adds the concept of one file (or set of files) containing configuration for multiple libraries (and maybe the application as well). As such, in addition to using shared files, the need to separate configuration into sections becomes necessary. By having each library have a dedicated section, the libraries maintain loose coupling and no settings will accidentally be used by multiple library with different meanings. `base_path` defines the path your library section.
    - `base_path` can be defined as a single key, a list of keys, or as a JSON Pointer (when the string start with `/`)
    - `base_path` keys must be strings.
    - Even for a one-off library, using a `base_path` can be useful for making configuration identifiable by contents and for enabling the library to join a shared configuration without requiring a breaking change.

### Library or application where the environment decides configuration files

```python
from granular_configuration_language import Configuration, LazyLoadConfiguration

CONFIG = LazyLoadConfiguration(
    Path(__file___).parent / "config.yaml",
    "~/.config/common_framework_config.yaml",
    base_path="really_cool_library",
    env_location_var_name="ORG_COMMON_CONFIG_LOCATIONS",
)
```

- Comments:
  - `env_location_var_name` specifies an optional environment variable that contains a comma-separated list of file paths.
    - Paths from the environment variable are appended to the end of list of explicit paths.
    - The environment variable is read at import time.

### Framework that only uses shared configuration files and does schema validation

```python
from granular_configuration_language import Configuration, LazyLoadConfiguration

CONFIG = LazyLoadConfiguration(
    base_path="really_cool_library",
    env_location_var_name="ORG_COMMON_CONFIG_LOCATIONS",
)
```

- Comments:
  - This case has been seen enough in the past that the caching of configurations was added for this option.
  - This case requires not having an embedded configuration.
    - Which means, defaults are defined programmatically, which means configuration is split between Python and YAML code, which is additional context switching and file search (one `config.yaml` vs. many `.py` files with one called `config.py`).
  - Use of [Pydantic](https://docs.pydantic.dev/latest/) is recommended for configuration validation and, if using, for defaulting.
    - Use a [cached](https://docs.python.org/3/library/functools.html#functools.cache) function to do Pydantic check, so the configuration stays cached during import time. Otherwise, each Pydantic check will flush the cache.

### Pulling configuration using wildcards

```python
from granular_configuration_language import Configuration, LazyLoadConfiguration

# Flat
CONFIG = LazyLoadConfiguration(
    *Path(__file___).parent.glob("*.yaml"),
    base_path="fixture-gen",
)
# Recursive
CONFIG = LazyLoadConfiguration(
    Path(__file___).parent / "fixture_config.yaml",
    *Path().rglob("fixture_config.yaml"),
    base_path="fixture-gen",
)
```

- Comments:
  - Flat: Sometimes it is useful separate subsections of a configuration into multiple files within the embedded configuration.
    - For example, your configuration has three types of things with twenty options per type. Having a file per type can make development easier and not having name specified can make it easier to add a fourth type.
  - Recursive: Sometimes it is useful to search current working directory for configuration.
    - For example, your library can generate fixtures for [`pytest`](https://docs.pytest.org/en/stable/). This enables to have fixtures declarations in the same directory as the test cases that use them.

---

## Writing your configuration

You are only limited by YAML syntax and your needs.

### Example

```yaml
example_config: # Example Base Path
  setting1: value
  setting2:
    sub_setting1: value
  example_of_codes:
    # This becomes Mapping[int, str]
    200: Success
    404: Not Found
```

### Things to bear in mind

- Take a look at the [YAML Tags](yaml.md) for options.
  - Use [`!PlaceHolder`](yaml.md#placeholder) to specify values the user need to provide.
- Setting names should be compatible Python attribute names.
  - This lets you use {py:meth}`~.LazyLoadConfiguration.__getattr__`.
- Use subsection to organize settings.
- Avoid you using non-string lookup keys.
  - `status_message_lookup: Mapping[int, str] = CONFIG.example_of_codes` is probably clearer than `success_message: str = CONFIG.example_of_codes[200]`
- A {py:class}`base_path <.LazyLoadConfiguration>` can be useful for making configuration identifiable by contents and for enabling the library to join a shared configuration without requiring a breaking change.
- Don't be afraid to comment your configuration when desired.
  - You may want your documentation to just point at your embedded configuration file.
- `key: ` specifies a value of {py:data}`None`. <!-- markdownlint-disable MD038 -->
  - Use `key: []` for an empty sequence or `key: {}` for an empty mapping.

### Type annotating your configuration

If you want code completion and typing checking, you can use {py:class}`.Configuration` like a {py:func}`dataclass <dataclasses.dataclass>` and {py:meth}`.LazyLoadConfiguration.as_typed` to apply your subclass.

```python
from collections.abc import Mapping
from granular_configuration_language import Configuration, LazyLoadConfiguration

class Setting2Config(Configuration):
    sub_setting1: str

class Config(Configuration):
    setting1: string
    setting2: Setting2Config
    example_of_codes: Mapping[int, str]

CONFIG = LazyLoadConfiguration(
  Path(__file___).parent / "config.yaml",
  base_path="example_config"
).as_typed(Config)
```

```{note}
This does not apply any runtime checks, just enables static code analysis.
```

---

## Using your configuration

You can fetch settings using {py:meth}`~.Configuration.__getattr__` or if you [Type annotate your configuration](#type-annotating-your-configuration):

```python
CONFIG.setting1
CONFIG.setting2.sub_setting1
CONFIG.example_of_codes
```

You can fetch settings using {py:meth}`~object.__getitem__`:

```python
CONFIG["setting1"]
CONFIG["setting2"]["sub_setting1"]
CONFIG["example_of_codes"]
```

Doing a runtime type check (using {py:meth}`~.Configuration.typed_get`):

```python
CONFIG.config.typed_get(str, "setting1")
CONFIG.config.typed_get(Configuration, "setting2").typed_get(str, "sub_setting1")
CONFIG.config.typed_get(Mapping[int, str], "example_of_codes")
```

If you need your settings as a {py:class}`dict` (using {py:meth}`~.Configuration.as_dict`):

```python
CONFIG.config.setting2.as_dict()
```

As JSON, using {py:mod}`json` (using ({py:meth}`~.Configuration.as_json_string`)):

```python
CONFIG.config.as_json_string()
```

Full specification at {py:class}`.Configuration` and {py:class}`.LazyLoadConfiguration`
