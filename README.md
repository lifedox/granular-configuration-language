# Granular Configuration library for Runtime-Loaded YAML Configurations for Python

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
from granular_configuration import LazyLoadConfiguration, ConfigurationLocations

CONFIG = LazyLoadConfiguration(
    ConfigurationLocations(files=['path1\to\configuration1.yaml']),
    ConfigurationLocations(
        filenames=["configuration2.yaml", "configuration2.yml"],
        directories=["path2\to"]
    ),
    ConfigurationLocations(
        filenames=("configuration3.yaml", "configuration3.yml"),
        directories=["path3\to"]
    ),
    base_path=["BasePath"])
```

**Runtime Usage:**
```python
assert CONFIG.Key1.Key2.Key3 == "Value"
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

## Tags

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

## Changelog
### 1.1
 * Adds `!Placeholder` Tag
 * Makes tags evaluate lazily (i.e. at first usage)
