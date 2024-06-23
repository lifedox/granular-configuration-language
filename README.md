# Granular Configuration library for Runtime-Loaded YAML Configurations for Python

This library allows a library or application to interact with typed settings that can be spread across separate configurations files that can have multiple locations, and allows for value overriding, enabling developer and application specify configurations that can be merged with library embedded configuration.

#### Common Names

- **Embedded Config**/**Package Config**: A configuration file the exists as package data within a library or application. Generally, a single file referenced via path to a `__file__`. This config should always exist in a library to defines defaults and form.
- **User Config**: A configuration file that exists in `~/.granular`.
- **Local Config**: A configuration file that exists in the current working directory.
- **Global Config**: The set of files called `global_config.yaml` or `global_config.yml` in the current working directory and/or `~/.granular`. See [Global Configuration](#Global-Configuration)

#### Quick Links

- [YAML Tags](#yaml-tags)
- [Base Path](#base-path)
- [Interface Objects](#interface-objects)
- [Patch Support](#patch-support)
- [Configuration Locations](#configuration-locations)
- [Changelog](#changelog)

#### Table of Contents

[TOC]

#

## Getting Started

While granular-configuration allows for many different ways to provide configuration to your application, here are two base examples as an easy way to get started.

### Application/Service example

In this example we are going to add a setting to call the inputs service.

Start by creating a `configs` folder and place a `configuration.yaml` file in it that looks like the following. This is your application's configuration file.

```yaml
myapi:
  inputs_svc:
    hostname: !Sub "https://inputs-svc.${CLUSTERNAME}"
```

The following is an example of accessing `hostname`:

```python
from granular_configuration import LazyLoadConfiguration
CONFIG = LazyLoadConfiguration("configs/configuration.yaml", base_path="myapi")
setting = CONFIG.inputs_svc.hostname
# or
setting = CONFIG["inputs_svc"]["hostname"]
```

If the `CLUSTERNAME` environment variable is `cluster.granular.ag`, then `setting` is `https://inputs-svc.cluster.granular.ag`.

There are no special names for the items in the config file. The names used in the config file (`myapi`, `inputs_svc` and `hostname`) can be anything you like. For instance, the `myapi` node is the root of your own service configuration. This can be any string you like but a good convention is to call it the same thing as your service or simply `api`. Use the `basepath` setting to scope your `CONFIG` variable to only contain your config values.

&nbsp;

Libraries can also use granular-configuration for their own config. Library consume settings from their own specific root key (typically the name of the library, please refer to the library documentation for configuration options).

An example of this is granular-db. To add granular-db connection settings to your config, extend your config to look like this.

```yaml
granular_db:
  # Note: This is not an example of the best usage of granular-db
  default:
    url: !Sub "postgresql://${DB_USER}:${DB_PASSWORD}@${POSTGRES_HOST}/mydb"
myapi:
  inputs_svc:
    hostname: !Sub "https://inputs-svc.${CLUSTERNAME}"
```

For the library to be able to find your config file, set the `G_CONFIG_LOCATION` environment variable to the location of your config file (see library section below).

&nbsp;

In both cases, the custom `!Sub` YAML tag is being used to resolve settings from runtime environment variables. Wherever possible use this to reduce the need for different config files for different environments.

If you follow standards for naming AWS resource ARNs, you can use this to set configs like this

```yaml
api:
  some_lambda_function:
    arn: !Sub "arn:aws:lambda:${REGION}:${AWS_ACCOUNT}:some_lambda_function"
```

The AWS related environment variables are typically set by our deployment jobs (k8s and lambdas etc.), making it easy for you to use in this way.

&nbsp;

### Library Example

For libraries, it is encouraged to provide an embedded configuration file with sane default values and environment variables for the user to set. This saves your users from having to define configuration that rarely change but an option to do so when needed.

Start by creating a `config` module and put a file named `embedded_config.yaml` in it (alongside `__init__.py`). The contents could be something like this.

```yaml
my-library:
  Setting1: !Sub "${ENV_VAR_THE_USER_HAS_TO_SET}" # Raise KeyError, if not set
  Setting2: !Sub "${ENV_VAR_THE_USER_CAN_TO_SET:-sane_default}" # Return "sane_default", if not set
  Setting3: "A sane default value"
```

To allow applications to override values in your config it should be read with a snippet similar to the one below (located next to `embedded_config.yaml` in `config`).

```python
CONFIG = LazyLoadConfiguration(
        Path(__file__).parent, "embedded_config.yaml",
        "~/my-library.*",  # Optional
        "./my-library.*",  # Optional,
        base_path=["my-library"],
        use_env_location=True,
    )
```

At runtime, this setup will read `embedded_config.yaml` from your package, `my-library.yaml` from the user's home directory and the current working directory, as well as any file specified in the `G_CONFIG_LOCATION` environment variable. It will prefer values in the opposite order with the embedded config being the last fallback.

Document all required and optional settings in your readme, so users know what to expect.

#

## Load Behavior Examples

### Multi-File Usage Example

**Example Config File:**

Path: `path1\to\configuration1.yaml`

```yaml
BasePath:
  Key1:
    Key2:
      Key3: Multi-Tiered Value Example
  CombinedExample:
    A: Set in configuration1.yaml
    B: Set in configuration1.yaml
```

Path: `path2\to\configuration2.yaml`

```yaml
BasePath:
  CombinedExample:
    B: Set in configuration2.yaml
    C: Set in configuration2.yaml
    D: Set in configuration2.yaml
```

Path: `path3\to\configuration3.yml`

```yaml
BasePath:
  CombinedExample:
    B: Set in configuration3.yml
    C: Set in configuration3.yml
    E: Set in configuration3.yml
```

**Setup:**
<br>Note: This library does not pre-defined any configuration or file locations

```python
from granular_configuration import LazyLoadConfiguration

CONFIG = LazyLoadConfiguration(
    'path1\to\configuration1.yaml', "path2\to\configuration2.y*", "path3\to\configuration3.y*",
    base_path=["BasePath"])
```

**Runtime Usage:**

```python
assert CONFIG.Key1.Key2.Key3 == "Multi-Tiered Value Example"
assert CONFIG.CombinedExample == {
    "A": "Set in configuration1.yaml"
    "B": "Set in configuration3.yml"
    "C": "Set in configuration3.yml"
    "D": "Set in configuration2.yaml"
    "E": "Set in configuration3.yml"
}
```

&nbsp;

### Precedents-Ordered File Example

- `.y*` defines a precedence order of `.yaml`, `.yml`.
- `.*` defines a precedence order of `.yaml`, `.yml`, `.ini`.

**Example Config File:**

Path: `path\to\configuration.yaml`

```yaml
BasePath1:
  Key1:
    Key2:
      Key3: Set by the priority file
```

Path: `path\to\configuration.yml`

```yaml
BasePath1:
  Key1:
    Key2:
      Key3: This file will not be read, because higher priority file exists
```

**Setup:**
<br>Note: This library does not pre-defined any configuration or file locations

```python
from granular_configuration import LazyLoadConfiguration, ConfigurationLocations

CONFIG = LazyLoadConfiguration(
    "path2\to\configuration.y*",
    base_path=["BasePath1"])
```

**Runtime Usage:**

```python
assert CONFIG.Key1.Key2.Key3 == "Set by the priority file"
```

&nbsp;

## Usage Patterns:

### Library Explicit

The library sets and owns where all of its configuration files can live.

#### Interface

```python
class LazyLoadConfiguration(object):
    """
    Provides a lazy interface for loading Configuration from ConfigurationLocations definitions on first access.
    """
    def __init__(
        self,
        *load_order_location: typ.Sequence[typ.Union[str, ConfigurationLocations]],
        base_path: typ.Optional[typ.Sequence[str]] -> None
    ) -> None:
        ...
```

#### Example

Inside Library

```python
from granular_configuration import LazyLoadConfiguration
import os

CONFIG = LazyLoadConfiguration(
    Path(__file__).parent / "embedded_config.yaml", # Required, since you should be using !Placeholder to represent the form, if there are no defaults
    "~/<lib_specific>_config.*", # Optional
    "./<lib_specific>_config.*", # Optional
    "global_config.*",
    base_path=["lib-base-path"]
)

```

Usage:

```python
from ... import ... CONFIG

CONFIG.setting
```

&nbsp;

### Env Variable

Regardless which of the above you use, if you provide the keyword argument use_env_location, the library will check the G_CONFIG_LOCATION, and append locations stored in this environment variable to the locations being used.

#### Example

Usage:

```python
from granular_configuration import LazyLoadConfiguration
CONFIG = LazyLoadConfiguration(use_env_location=True)
```

&nbsp;

## Interface Objects

### `Configuration`

The `Configuration` acts similarly to an `attrdict`, with the exception being that calling `__getattr__` (reminder: `CONFIG.key` is the same as `CONFIG.__getattr__("key")`) on a missing element will throw a `KeyError` instead of creating a new `Configuration` (This is due to design differences, `attrdict` expects user-codebase to construct the object, whereas this library constructs the object and provides it to user-codebase).

This object acts like a dictionary and has been hacked to pass `instance(CONFIG, dict)` and can be copied via `copy.copy` and `copy.deepcopy` safely.

_Interface Definition:_

```python
import typing as typ

class Configuration(typ.MutableMapping[typ.Any, typ.Any]):
    def __getattr__(self, name: str) -> typ.Union[typ.Any, "Configuration"]:
        """
        Provides potentially cleaner path as an alternative to __getitem__.
        Throws AttributeError instead of KeyError, as compared to __getitem__ when an attribute/key is not present.
        """
        ...

    def exists(self, key: typ.Any) -> bool:
        """
        Checks that a key exists and is not a Placeholder
        """
        ...

    def as_dict(self) -> typ.Dict[typ.Any, typ.Any]:
        """
        Returns the Configuration settings as standard Python dict.
        Nested Configartion object will also be converted.
        This will evaluated all lazy tag functions and throw an exception on Placeholders.
        """
        ...

    def patch(self,
        patch_map: typ.Mapping[typ.Any, typ.Any],
        allow_new_keys: bool = False
    ) -> typ.ContextManager:
        """
        Provides a Context Manger, during whose context's values returned by this Configuration are
        replaced with the provided patch values.
        """


```

See [Patch Support](#patch-support) for details of `patch`

Note: The reason for keys being `typing.Any` is that the YAML allows keys to be more than strings (i.e. integer, float, boolean, null), and this library does not restrict this (as there a valid reasons to want to have an integer-to-string map and so on). Just note that you cannot used the `__getattr___` with keys that do not meet the Python attribute naming restrictions, you would have to look those up via `__getitem__` (i.e. `CONFIG[1]`).

&nbsp;

### `LazyLoadConfiguration`

The build and loader of Configuration that acts as the interface for the root Configuration object.

**Standard Code Pattern:**

Submodule Structure:

- `config`
  - `__init__.py`
  - `_config.py`
  - `<embedded>_config.yaml`

`__init__.py`:

```python
from absolute_module_path.config._config import CONFIG
```

`_config.py`:

```python
import os
from granular_configuration import ConfigurationFiles, ConfigurationMultiNamedFiles, LazyLoadConfiguration


CONFIG = LazyLoadConfiguration(
    Path(__file__).parent /  "<embedded>_config.yaml",
    "~/.granular/<special>_config.*",
    "./<special>_config.*",
    "~/.granular/global_config.*",
    "./global_config.*",
    base_path=["<UniqueBasePath>"])
```

_Interface Definition:_

```python
import typing as typ

class LazyLoadConfiguration(object): # __getattr__ implies implementing Configuration's protocol
    """
    Provides a lazy interface for loading Configuration from ConfigurationLocations definitions on first access.
    """
    def __init__(
        self,
        *load_order_location: typ.Sequence[typ.Union[str, ConfigurationLocations]],
        base_path: typ.Optional[typ.Union[str, typ.Sequence[str]]] = None
    ) -> None:
        ...


    def __getattr__(self, name: str) -> typ.Any:
        """
        Loads (if not loaded) and fetches from the underlying Configuration object.
        This also exposes the methods of Configuration.
        """
        ...

    def load_configuration(self) -> None:
        """
        Force load the configuration.
        """
        ...

    @property
    def config(self) -> Configuration:
        """
        Loads and fetches the underlying Configuration object
        """
        ...
```

Note: This class does not inherit from `Configuration`, `MutableMapping`, or `dict`. It provides access to the methods of `Configuration`, but checks against type (e.g. such as `json.dumps`) should done against `LazyLoadConfiguration.config`.

&nbsp;

## Patch Support

_Interface Definition:_

```python
import typing as typ

class Configuration(typ.MutableMapping[typ.Any, typ.Any]):
    def patch(self,
        patch_map: typ.Mapping[typ.Any, typ.Any],
        allow_new_keys: bool = False
    ) -> typ.ContextManager:
        """
        Provides a Context Manger, during whose context's values returned by this Configuration are
        replaced with the provided patch values.
        """
```

<br>

`patch` provides an ability to temporary changes settings on a `Configuration` object. It exists primarily for testing.

By default, patch will not allow new setting keys to be added, this can be altered by passing `allow_new_keys=True`, but all nested patches must called with this argument.

Patches are <u>not</u> type-check against current values.

### Examples

#### Simple Setting

```python
from attrdict import AttrDict
from granular_configuration import Configuration

CONFIG = Configuration(
    key1="value1",
    key2="value2",
    nested=Configuration(
        nest_key1="nested_value1",
        nest_key2="nested_value2"
    )
)

patch1 = AttrDict()
patch1.key1 = "new value"

with CONFIG.patch(patch1):
    print(CONFIG)
    assert CONFIG.key1 == "new value"

```

Output:

```python
{
    'key1': 'new value',
    'key2': 'value2',
    'nested': {
        'nest_key1': 'nested_value1',
        'nest_key2': 'nested_value2'
    }
}
```

#### Nested Settings

```python
from attrdict import AttrDefault
from granular_configuration import Configuration

CONFIG = Configuration(
    key1="value1",
    key2="value2",
    nested=Configuration(
        nest_key1="nested_value1",
        nest_key2="nested_value2"
    )
)

patch1 = AttrDefault(AttrDefault)
patch1.key1 = "new value"
patch1.nested.nest_key2 = "new value"

with CONFIG.patch(patch1):
    print(CONFIG)
    assert CONFIG.key1 == "new value"
```

Output:

```python
{
    'key1': 'new value',
    'key2': 'value2',
    'nested': {
        'nest_key1': 'nested_value1',
        'nest_key2': 'new value'
    }
}
```

#### Adding Settings

```python
from attrdict import AttrDefault
from granular_configuration import Configuration

CONFIG = Configuration(
)

patch1 = AttrDefault(AttrDefault)
patch1.key1 = "new value"
patch1.nested.nest_key2 = "new value"

with CONFIG.patch(patch1, allow_new_keys=True):
    print(CONFIG)
    assert CONFIG.key1 == "new value"
```

Output:

```python
{
    'key1': 'new value',
    'nested': {
        'nest_key2': 'new value'
    }
}
```

#### Nested Patches Settings

```python
from attrdict import AttrDefault
from granular_configuration import Configuration

CONFIG = Configuration(
    key1="value1",
    key2="value2",
    nested=Configuration(
        nest_key1="nested_value1",
        nest_key2="nested_value2",
    )
)

patch1 = AttrDefault(AttrDefault)
patch1.key1 = "new value"
patch1.nested.nest_key2 = "new value"

patch2 = AttrDefault(AttrDefault)
patch2.key2 = "new value2"
patch2.nested.nest_key1 = "new value2"


with CONFIG.patch(patch1):
    with CONFIG.patch(patch2):
        print(CONFIG)
```

Output:

```python
{
    'key1': 'new value',
    'key2': 'new value2',
    'nested': {
        'nest_key1': 'new value2',
        'nest_key2': 'new value'
    }
}
```

&nbsp;

## Configuration Locations

**For clarity it is recommend to use string paths with `.*` or `.yaml`, as argument for `LazyLoadConfiguration`**

Order for loading your is highly important, as each successive configuration file can provide overrides to values to the previous. `LazyLoadConfiguration` takes in a list (as `*args`) of ConfigurationLocations objects or strings that each provides as list of configuration files to load. By intermixing provided objects, you should be able to clearly and tightly define the load order of your configuration and what happens when files do not exist.

When providing only strings to `LazyLoadConfiguration` they will automatically be converted in `ConfigurationFiles`, `ConfigurationMultiNamedFiles`. Paths with the file extension `.*` will be converted in `ConfigurationMultiNamedFiles(directories=(dirname), filenames=(basename.yaml, basename.yml, basename.ini)` Paths with the files extensions `.y*` and `.yml` will be converted in `ConfigurationMultiNamedFiles(directories=(dirname), filenames=(basename.yaml, basename.yml)` Paths with the file extension `.ini` will be converted in `ConfigurationMultiNamedFiles(directories=(dirname), filenames=(basename.ini, basename.yaml, basename.yml)`

Note: Duplicate file definitions are ignored and used in the first order found.

&nbsp;

### `ConfigurationFiles`

This is the simplest definition. Takes in a list of files and outputs all the files that exists.

_Interface Definition:_

```python
import typing as typ

class ConfigurationFiles(ConfigurationLocations):
    def __init__(self, files: typ.Sequence[str]) -> None:
        ...

    @classmethod
    def from_args(cls, *files: typ.Sequence[str]) -> "ConfigurationFiles":
        ...
```

&nbsp;

### `ConfigurationMultiNamedFiles`

Takes in a list of possible filenames and directories, using only the first filename that exists per directory.

Example:
Note: The order of the directories in this example is not an absolute pattern, there are valid cases from the user config taking precedence over the current working directory.

```python
locations = ConfigurationMultiNamedFiles(
    filenames=['config.yaml', 'config.yml'],
    directories=(Path("~/.granular/"), os.getcwd())
).get_locations()
```

Cases:

- If only `./config.yaml` exists, then `locations` will be `['./config.yaml']`
- If `./config.yaml` and `./config.yml` exists, then `locations` will be `['./config.yaml']`
- If `./config.yml` and `~/.granular/config.yml` exists, then `locations` will be `['~/.granular/config.yml', './config.yaml']`

_Interface Definition:_

```python
import typing as typ

class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames: typ.Sequence[str], directories: typ.Sequence[str]) -> None:
        ...
```

&nbsp;

## Base Path

**Use of a Base Path is strongly recommended for all codebases that used this library**

Base Path is a load time filter of Configuration File. It allows for configuration settings to be partitioned and isolated, allowing a single configuration file to provide configuration for many libraries and application, while preventing configuration settings from being applied incorrectly due to incorrectly name files.

**Example:**

Config:

```yaml
Level1:
  Level2:
    Level3:
      a: 1
```

Output Examples:

```python
assert LazyLoadConfiguration(..., base_path=[]).as_dict() == {"Level1": {"Level2": {"Level3": {"a": 1}}}}
assert LazyLoadConfiguration(..., base_path=["Level1"]).as_dict() == {"Level2": {"Level3": {"a": 1}}}
assert LazyLoadConfiguration(..., base_path=["Level1", "Level2", "Level3"]).as_dict() == {"a": 1}
```

&nbsp;

## YAML Tags

- `!Sub`
  - **Usage:** `!Sub ${ENVIRONMENT_VARIABLE_THAT_EXISTS} ${ENVIRONMENT_VARIABLE_THAT_DOES_NOT_EXIST:-default value} ${$.jsonpath.expression}`
  - **Argument:** _str_.
  - **Returns:** a string produced by the string format
  - Interpolations:
    - `${ENVIRONMENT_VARIABLE_THAT_EXISTS}`: Replaced with the specific Environment Variable. Raises `KeyError`, if the variable does not exist.
    - `${ENVIRONMENT_VARIABLE_THAT_EXISTS:-default value}`: (Note: specifier is `:-`, following BASH style) Replaced with the specific Environment Variable, or the provided default.
    - `${$.jsonpath.expression}`: Replaced by the the object in the configuration specified in JSON Path syntax.
      - Paths must start at full root of configuration, using `$` as the first character.
      - Results:
        - Paths that define one object will be `str`-ed.
        - Paths that return many objects will be the `repr` of the list.
        - Paths that return nothing raise `KeyError`.
    - `${...}`: This Tag is greedy and grabs all substrings (unlike `!Env`) and does not provide escapes. Please, request escapes if they are needed.
    - `$(...)` and `$[...]` are reserved future for use, but are not blocked for use.
    - Note: This is a recursible function. Any cycles can cause infinite loops.
- `!Env`
  - **Usage:** `!Env '{{ENVIRONMENT_VARIABLE_THAT_EXISTS}} {{ENVIRONMENT_VARIABLE_THAT_DOES_NOT_EXIST:default value}}'`
  - **Argument:** _str_.
  - **Returns:** a string produced by the string format, replacing `{{VARIABLE_NAME}}` with the Environment Variable specified. Optionally, a default value can be specified should the Environment Variable not exist.
  - Note: `!Sub` replaces this functionality and offers more options. `!Env` will not be removed but will not see future updates.
- `!ParseEnv`
  - **Usage:** `!ParseEnv ENVIRONMENT_VARIABLE` or `!ParseEnv [ENVIRONMENT_VARIABLE, <YAML object>]`
  - **Argument:** _Union[str, Tuple[str, Any]_.
  - **Returns:**
    - If provided a string, the Environment Variable specified will be parsed as YAML. If the Environment Variable does not exist, an error will be thrown.
    - If provided a sequence, the second object will be returned, if the Environment Variable does not exists, instead of erroring.
  - Note: This is a recursible function. `!ParseEnv VAR`, where `VAR='!ParseEnv VAR'` will loop until the call stack reaches maximum depth.
- `!Func`
  - **Usage:** `!Func 'path.to.function'`
  - **Argument:** _str_.
  - **Returns:** a pointer to the function specified. Acts as an import of `path.to`, returning `getattr(path.to, function)`. The current working directory is added prior to attempt the import. Returned object must be callable.
- `!Class`
  - **Usage:** `!Class 'path.to.function'`
  - Acts the same as `!Func` except that the returned object must subclass `object`
- `!Placeholder`
  - **Usage:** `!Placeholder 'message'`
  - **Argument:** _str_.
  - **Returns:** a `Placeholder` containing the message. If a Placeholder is not overridden, a `PlaceholderConfigurationError` exception will be thrown if accessed.

&nbsp;

## Global Configuration

The global configuration is defined to be `global_config.yaml` available in the current working directory or the `~/.granular/` directory. The global provides allows developers and deployed applications to have a single configuration file to many libraries and applications, using Base Path to partition and isolate a single codebase's configuration.

Add these path strings to your `LazyLoadConfiguration` to support the Global Config:

```python
LazyLoadConfiguration(
   ...,
   "./global_config.*", "~/.granular/global_config.*",
   ...,
)
```

&nbsp;

## Changelog

### 2.0.0

- Removed `set_config` pattern
- Removed INI support
- Switched from `PyYAML` to ruamel.yaml
  - Note: `PyYAML` is very dead
  - This primarily means YAML Version 1.2 is the default supported version.
    - `yes/no`, `y/n`, `on/off` is no longer `bool`
    - Octal support is clearer: `010` means 10, `0o10` means 8.
  - YAML 1.1 support can be explicit enabled by using the `%YAML 1.1 ---` directive
- Switched from `jsonpath-rw` to `python-jsonpath`
  - Note: `jsonpath-rw` is very dead
  - Important: Both `jsonpath-rw` and `python-jsonpath` cannot be install. `jsonpath-rw` controls `jsonpath_rw` and `jsonpath` modules (despite not explicitly needing the latter). `python-jsonpath` also controls `jsonpath`, but losses in `jsonpath-rw`.
    - `ImportError` occur on the `jsonpath` modules when both are install.
- Renamed `granular_configuration.yaml_handler` module to `granular_configuration.yaml`

### 1.8.0

- Adds `!Sub` Tag

### 1.5.0

- Adds `!ParseEnv` Tag

### 1.4.0

- Adds InvalidBasePathException as an exception the can be thrown during the load phase of `LazyLoadConfiguration`.
  - This subclasses `KeyError` maintaining compatibility with the state before this exception.
- `LazyLoadConfiguration`'s `base_path` argument now takes a single `str` in addition to the original `typing.Sequence[str]`

### 1.3.1

- Adds clear_config

### 1.3

- Adds string path support to `LazyLoadConfiguration`
- Adds get-config pattern
- Adds Configuration.patch

### 1.2

- Adding ini support

### 1.1

- Adds `!Placeholder` Tag
- Makes tags evaluate lazily (i.e. at first use)

## Author

Code Owner: Eric Jensen (ericjensen@granular.ag)
