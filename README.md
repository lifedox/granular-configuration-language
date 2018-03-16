# Granular Configuration library for Runtime-Loaded YAML Configurations for Python

## Basic Usage Example

**Example Config File:**
```yaml
BasePath:
  Key1:
    Key2:
      Key3: Value
```

**Setup:**
<br>Note: This library does not pre-defined any configuration or file locations
```python
from granular_configuration import LazyLoadConfiguration, ConfigurationLocations
import os

CONFIG = LazyLoadConfiguration(
    ConfigurationLocations(files=[os.path.join(os.path.dirname(__file__), "es_config.yaml")]),
    ConfigurationLocations(filenames=("es_client_config.yaml", "es_client_config.yml"),
                           directories=(os.getcwd(), os.path.expanduser("~/.granular/"))),
    ConfigurationLocations(filenames=("global_config.yaml", "global_config.yml"),
                           directories=(os.getcwd(), os.path.expanduser("~/.granular/"))),
    base_path=["BasePath"])
```

**Runtime Usage:**
```python
assert CONFIG.Key1.Key2.Key3 == "Value"
```
