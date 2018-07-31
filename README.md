# Granular Configuration library for Runtime-Loaded YAML Configurations for Python

This library allows a library or application to interact with typed settings that can be spread across separate configurations files that can have multiple locations, and allows for value overriding, enabling developer and application specify configurations that can be merged with library embedded configuration.


#### Common Names
- **Embedded Config**: A configuration file the exists as package data within a library or application. Generally, a single file (referenced via path to a `__file__`) loaded via `ConfigurationFiles`
- **User Config**: A configuration file that exists in `~/.granular`.
- **Local Config**: A configuration file that exists in the current working directory.
- **Global Config**: The set of files called `global_config.yaml` or `global_config.yml` in the current working directory and/or `~/.granular`. See [Global Configuration](#Global-Configuration)


#### Quick Links
- [YAML Tags](#yaml-tags)
- [Configuration Locations](#configuration-locations)
- [Interface Objects](#interface-objects)
- [Base Path](#base-path)
- [Changelog](#changelog)
- [Ini Configuration File Support](#ini-configuration-file-support)


## Examples

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
from granular_configuration import LazyLoadConfiguration, ConfigurationFiles, ConfigurationMultiNamedFiles

CONFIG = LazyLoadConfiguration(
    ConfigurationFiles(files=['path1\to\configuration1.yaml']),
    ConfigurationMultiNamedFiles(
        filenames=["configuration2.yaml", "configuration2.yml"],
        directories=["path2\to"]
    ),
    ConfigurationMultiNamedFiles(
        filenames=("configuration3.yaml", "configuration3.yml"),
        directories=["path3\to"]
    ),
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
    ConfigurationLocations(
        filenames=["configuration.yaml", "configuration.yml"],
        directories=["path2\to"]
    ),
    base_path=["BasePath1"])
```

**Runtime Usage:**
```python
assert CONFIG.Key1.Key2.Key3 == "Set by the priority file"
```

&nbsp;

## Configuration Locations

Order for loading your is highly important, as each successive configuration file can provide overrides to values to the previous. `LazyLoadConfiguration` takes in a list (as `*args`) of ConfigurationLocations objects that each provides as list of configuration files to load. By intermixing provided objects, you should be able to clearly and tightly define the load order of your configuration and what happens when files do not exist.

Note: Duplicate file definitions are ignored and used in the first order found.

&nbsp;

### `ConfigurationFiles`

This is the simplest definition. Takes in a list of files and outputs all the files that exists.

*Interface Definition:*
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

Takes in a list of possibles filenames and directories, using only the first filename that exists per directory.

Example:
Note: The order of the directories in this example is not an absolute pattern, there are valid cases from the user config taking precedence over the current working directory.

```python
locations = ConfigurationMultiNamedFiles(
    filenames=['config.yaml', 'config.yml'],
    directories=(os.path.expanduser("~/.granular/"), os.getcwd())
).get_locations()
```

Cases:
- If only `./config.yaml` exists, then `locations` will be `['./config.yaml']`
- If `./config.yaml` and `./config.yml` exists, then `locations` will be `['./config.yaml']`
- If `./config.yml` and `~/.granular/config.yml` exists, then `locations` will be `['~/.granular/config.yml', './config.yaml']`


*Interface Definition:*
```python
import typing as typ

class ConfigurationMultiNamedFiles(ConfigurationLocations):
    def __init__(self, filenames: typ.Sequence[str], directories: typ.Sequence[str]) -> None:
        ...
```

&nbsp;

## Interface Objects

### `Configuration`

The `Configuration` acts similarly to an `attrdict`, with the exception being that calling `__getattr__` (reminder: `CONFIG.key` is the same as `CONFIG.__getattr__("key")`) on a missing element will throw a `KeyError` instead of creating a new `Configuration` (This is due to design differences, `attrdict` expects user-codebase to construct the object, whereas this library constructs the object and provides it to user-codebase).

This object acts like a dictionary and has been hacked to pass `instance(CONFIG, dict)` and can be copied via `copy.copy` and `copy.deepcopy` safely.

*Interface Definition:*
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

```

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
    ConfigurationFiles([os.path.join(os.path.dirname(__file__), "<embedded>_config.yaml")]),
    ConfigurationMultiNamedFiles(filenames=("<special>_config.yaml", "<special>_config.yml"),
                                 directories=(os.path.expanduser("~/.granular/"),
                                              os.getcwd())),
    ConfigurationMultiNamedFiles(filenames=("global_config.yaml", "global_config.yml"),
                                 directories=(os.path.expanduser("~/.granular/"),
                                              os.getcwd())),
    base_path=["<UniqueBasePath>"])


```

*Interface Definition:*
```python
import typing as typ

class LazyLoadConfiguration(object):
    """
    Provides a lazy interface for loading Configuration from ConfigurationLocations definitions on first access.
    """

    def __getattr__(self, name: str) -> typ.Any:
        """
        Loads (if not loaded) and fetches from the underlying Configuration object.
        This also exposes the methods of Configuration.
        """
        ...

    def load_configure(self) -> None:
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

* `!Env`
  - **Usage:** `!Env '{{ENVIRONMENT_VARIABLE_THAT_EXISTS}} {{ENVIRONMENT_VARIABLE_THAT_DOES_NOT_EXIST:default value}}'`
  - **Argument:** *String*. Returns a string produced by the string format, replacing `{{VARIABLE_NAME}}` with the Environment Variable specified. Optionally, a default value can be specified should the Environment Variable not exist.
* `!Func`
  - **Usage:** `!Func 'path.to.function'`
  - **Argument:** *String*. Returns a pointer to the function specified. Acts as an import of `path.to`, returning `getattr(path.to, function)`. The current working directory is added prior to attempt the import. Returned object must be callable.
* `!Class`
  - **Usage:** `!Class 'path.to.function'`
  - Acts the same as `!Func` except that the returned object must subclass `object`
* `!Placeholder`
  - **Usage:** `!Placeholder 'message'`
  - **Argument:** *String*. Returns a `Placeholder` containing the message. If a Placeholder is not overridden, a `PlaceholderConfigurationError` exception will be thrown if accessed.

&nbsp;

## Global Configuration

The global configuration is defined to be `global_config.yaml` available in the current working directory or the `~/.granular/` directory. The global provides allows developers and deployed applications to have a single configuration file to many libraries and applications, using Base Path to partition and isolate a single codebase's configuration.


Add this `ConfigurationMultiNamedFiles` to your `LazyLoadConfiguration` to support the Global Config:

```python
    ConfigurationMultiNamedFiles(filenames=("global_config.yaml", "global_config.yml"),
                                 directories=(os.path.expanduser("~/.granular/"),
                                              os.getcwd())),
```


&nbsp;

## Ini Configuration File Support

Configuration files will be loaded as a YAML file unless they have a file extension of `.ini`. INI files will be load via an extended INI feature set.

#### General Notes
- Use of the `[DEFAULT]` is highly discouraged.
- Use of `[ROOT]`, while added for completeness, is also discouraged, as Base Paths are highly encouraged.
- Support of only INI configuration is highly discouraged, as well.
- List values should be define using JSON syntax (e.g `key=['a', 'b', 'c']`), not delimited text that is parse by the user-codebase
- YAML will always be recommended over INI, as INI features are nonstandard and basically a wrapper over a subset of YAML features.

#### Loading

The file loader type is selected purely on file extension.

This example always, an INI file at `./<special>_config.ini` or `~/.granular/<special>_config.ini` to be used if the .yaml or .yml are not available.

```python
from granular_configuration import ConfigurationFiles, ConfigurationMultiNamedFiles, LazyLoadConfiguration

CONFIG = LazyLoadConfiguration(
    ConfigurationFiles([os.path.join(os.path.dirname(__file__), "<embedded>_config.yaml")]),
    ConfigurationMultiNamedFiles(filenames=("<special>_config.yaml", "<special>_config.yml", , "<special>_config.ini"),
                                 directories=(os.path.expanduser("~/.granular/"),
                                              os.getcwd())),
    ConfigurationMultiNamedFiles(filenames=("global_config.yaml", "global_config.yml"),
                                 directories=(os.path.expanduser("~/.granular/"),
                                              os.getcwd())),
    base_path=["<UniqueBasePath>"])
```


#### Nested Mappings

Support for nested mappings is provided through `.` delimited section name. Base Path support for INI appears as a prefix.

**Note: Compound Nodes are order sensitive**. From example, `CompoundKey` with its scaler attributes must be defined before `CompoundKey.comp_key3`

**Example:**
```ini
[ROOT]
root_key1=value1
root_key2=value2

[CompoundKey]
comp_key1=value3
comp_key2=value4

[CompoundKey.comp_key3]
nested_key1=value5

[NewCompoundKey.comp_key4]

```

loads as the following Python dict:
```python
{
  "root_key1": "value1",
  "root_key2": "value2",
  "CompoundKey": {
    "comp_key1": "value3",
    "comp_key2": "value4",
    "comp_key3": {
      "nested_key1": "value5"
    }
  },
  "NewCompoundKey": {
    "comp_key4": {}
  }
}
```

as YAML:
```yaml
root_key1: value1
root_key2: value2
CompoundKey:
  comp_key1: value3
  comp_key2: value4
  comp_key3:
    nested_key1: value5
NewCompoundKey:
  comp_key4: {}
```

&nbsp;

#### Type Support

The INI spec defines always keys and values to be string. In order to support the full feature set of types supported by YAML, all keys and values parsed as YAML, enabling boolean, float, integer, null, tag, and list support. **This means all keys and values must be valid single-node YAML**

**Example:**
```ini
[BasePath]
tagged_key=!Env '{{VARIABLE_THAT_DOES_NOT_EXIST:default value}}'
func_key=!Func functools.reduce
string_key2=string with spaces

[BasePath.IntMap]
404=NotFound
500=GeneralError

[BasePath.LessUsefulMap]
null=1
True=False
1.123=!Class collections.defaultdict
"1"='1'
```

loads as the following Python dict:
```python
{
  'BasePath': {
    'tagged_key': 'default value',
    'func_key': reduce,
    'string_key2': 'string with spaces',
    'IntMap': {
        404: 'NotFound',
        500: 'GeneralError'
    },
    'LessUsefulMap': {
        None: 1,
        True: False,
        1.123: collections.defaultdict,
        '1': '1'
    }
  }
}

```

as YAML:
```yaml
BasePath:
  tagged_key: !Env '{{VARIABLE_THAT_DOES_NOT_EXIST:default value}}'
  func_key: !Func functools.reduce
  string_key2: string with spaces
  IntMap:
    404: NotFound
    500: GeneralError
  LessUsefulMap:
    null: 1
    true: False
    1.123: !Class collections.defaultdict
    '1': "1"
```

&nbsp;

## Changelog

### 1.2
 * Adding ini support

### 1.1
 * Adds `!Placeholder` Tag
 * Makes tags evaluate lazily (i.e. at first usage)
