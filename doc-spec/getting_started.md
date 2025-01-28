# Getting Started

## Defining a Configuration

Configuration is always defined by constructing a {py:class}`.LazyLoadConfiguration` and providing the paths to possible files. Paths can be {py:class}`str` or {py:class}`pathlib.Path` objects.

Examples:

### One-off library with three possible sources

```python
CONFIG = LazyLoadConfiguration(
    Path(__file___).parent / "config.yaml",
    "~/.config/really_cool_library_config.yaml",
    "./really_cool_library_config.yaml",
)
```

- Comments:
  - `Path(__file___).parent /` creates a file relative directory. Using this ensures that the embedded configuration (the one shipped with this library) is correctly reference within site-package.
    - ⚠️ Don't forget to add the embedded config to package data.
  - `~/.config/` is useful when you have settings that developers may want to on their machines.
    - For example, plain text logs while debugging and JSON logs for deploys.
  - `./` is useful for application deployment-specific settings.
    - For example, say we have an application deploying to a Lambda package and a container service. With a current working directory option, Lambda specific settings and the container specific settings are single file addition to common deploy package.

### Library that shares configuration files with other libraries

```python
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
CONFIG = LazyLoadConfiguration(
    base_path="really_cool_library",
    env_location_var_name="ORG_COMMON_CONFIG_LOCATIONS",
)
```

- Comments:
  - This case has been seen enough in the past that the caching of configurations was added for this option.
  - This case requires not having a library-specific configuration.
    - Which means, defaults are defined programmatically, which means configuration is split between Python and YAML code, which is additional context switching and file search (one `config.yaml` vs. many `.py` files with one called `config.py`).
  - Use of [Pydantic](https://docs.pydantic.dev/latest/) is recommended for configuration validation and defaulting.
    - Use a [cached](https://docs.python.org/3/library/functools.html#functools.cache) function to do Pydantic check, so the configuration stays cached during import time. Otherwise, each Pydantic check will flush the cache.

### Pulling configuration using wildcards

```python
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
  - Flat: Sometimes it is useful separate subsections of a configuration into multiple files within the library-specific configuration.
    - For example, your configuration has three types of things with twenty options per type. Having a file per type can make development easier and not having name specified can make it easier to add a fourth type.
  - Recursive: Sometimes it is useful to search current working directory for configuration.
    - For example, your library can generate fixtures for [`pytest`](https://docs.pytest.org/en/stable/). This enables to have fixtures declarations in the same directory as the test cases that use them.

---

## Writing your configuration

TODO

---

## Using your configuration

TODO
