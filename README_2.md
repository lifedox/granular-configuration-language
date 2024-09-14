# `a-granular-configuration`

[TOC]

## Why does this exist?

This library exists to allow your code use YAML as a configuration language for internal and external parties.

Some use cases:

- You are writing a library to help connect to some databases. You want users to easily changes settings and defined databases by name.
  - Conceptual Example:
    - Library Code:
      ```python
      CONFIG = LazyLoadConfiguration(
        Path(__file___).parent / "config.yaml",
        "./database-util-config.yaml",
        "~/configs/database-util-config.yaml",
        base_path="database-util",
        env_location_var_name="ORG_COMMON_CONFIG_LOCATIONS",
        use_env_location=True,
      )
      ```
    - Library configuration:
      ```yaml
      database-util:
        common_settings:
          use_decimal: true
          encryption_type: secure
        databases: {} # Empty mapping, for users define
      ```
    - User application configuration:
      ```yaml
      database-util:
        common_settings:
          use_decimal: false
        databases:
          datebase1:
            location: http://somewhere
            user: !Mask ${DB_USERNAME}
            password: !Mask ${DB_PASSWORD}
        ```
- You are deploying an application that has multiple deployment types with specific settings.
  - Conceptual Example:
    - Library Code:
      ```python
      CONFIG = LazyLoadConfiguration(
        Path(__file___).parent / "config.yaml",
        "./database-util-config.yaml",
        base_path="app",
      )
      ```
    - Base configuration:
      ```yaml
      app:
        log_as: really cool app name
        log_to: nowhere
      ```
    - AWS Lambda deploy:
      ```yaml
      app:
        log_to: std_out
      ```
    - Server deploy:
      ```yaml
      app:
        log_to: !Sub file://var/log/${app.log_as}.log
      ```
- You are writing a `pytest` plugin that create test data using named fixtures configured by the user.
  - Conceptual Examples:
    - Library Code:
      ```python
      CONFIG = LazyLoadConfiguration(
        Path(__file___).parent / "fixture_config.yaml",
        *Path().rglob("fixture_config.yaml"),
        base_path="fixture-gen",
      ).config
      #
      for name, spec in CONFIG.fixtures:
        generate_fixture(name, spec)
      ```
    - Library configuration:
      ```yaml
      fixture-gen:
        fixtures: {} # Empty mapping, for users define
      ```
    - User application configuration:
      ```yaml
      fixture-gen:
        fixtures:
          fixture1:
            api: does something
      ```

---

## Lifecycle

1. **Import Time**: `LazyLoadConfiguration`'s are defined (`CONFIG = LazyLoadConfiguration(...)`).
   - So long as the next step does not occur, all identical immutable configurations identified and marked for caching.
     - Moving the next step clears the cache for all identical immutable configurations, meaning if another identical immutable configuration create will be loaded separately.
2. **First Fetch**: Configuration is fetched for the first time (through `CONFIG.value`, `CONFIG[value]`, `CONFIG.config`, and such)
   1. **Load Time**:
      1. The file system is scanned for specified configuration files.
      2. Each file is read and parsed.
   2. **Merge Time**:
      - Any Tags defined at the root of the file are run (i.e. the file beginning with a tag: `!Parsefile ...` or `!Merge ...`).
      - The loaded Configurations are merged in-order into one Configuration.
        - Any files that do not define a Mapping are filtered out.
        - Mappings are merged recursively. Any non-mapping overrides. Newer values override older values.
          - `{"a": "b": 1}` + `{"a: {"b": {"c": 1}}` ⇒ `{"a: {"b": {"c": 1}}`
          - `{"a: {"b": {"c": 1}}` + `{"a: {"b": {"c": 2}}` ⇒ `{"a: {"b": {"c": 2}}`
          - `{"a: {"b": {"c": 2}}` + `{"a: {"b": {"d": 3}}` ⇒ `{"a: {"b": {"c": 2, "d": 3}}`
          - `{"a: {"b": {"c": 2, "d": 3}}` + `{"a": "b": 1}` ⇒ `{"a": "b": 1}`
   3. **Build Time**:
      1. The Base Path is applied.
      2. The Base Paths for any `LazyLoadConfiguration` shared this identical immutable configuration is applied.
         - Exceptions that occur (such as `InvalidBasePathException`) are stored, so they emit for the first fetch of the associated `LazyLoadConfiguration`.
      3. `LazyLoadConfiguration` no longer holds a reference to the root object. If no tags depend on the root Configuration, it will be free (`!Sub` is an example of a tag that holds a reference to the root Configuration until it is run).
         - If an exception occurs, the root Configuration is unavoidable caught in the frame.
3. **Fetching a Lazy Tag**:
   1. Upon first get of the `LazyEval` object, the underlying function is called.
   2. The result replaces the `LazyEval` in the Configuration, so the `LazyEval` run exactly once.

When making copies, it is important to note that `LazyEval` do not copy (they return themselves). This is to aid in running exactly once and prevent cycles with the root reference.

This means that a deep copy of a `Configuration` can share state with the original, if any `LazyEval` is present. Using immutable `Configuration` (and `MutableConfiguration`) will prevent needing to make copies. `as_dict()` is also a great way to make a mutable copy.

---

## YAML Tags

- **Argument** and **Return** use Python primitive type as common reference.
  - To convert to YAML node definitions:
    - `Any` is any type.
    - `str` is "scalar"
    - `list` is "sequence"
    - `tuple` is a sized "sequence"
    - `dict` is "mapping"
      - All "mapping" mapping nodes return as a `Configuration`.
        - Or `MutableConfiguration`, when `mutable=True`.
  - Tags in YAML only support "scalar", "sequence", and "mapping".
    - As such,`!Tag 1.0` is always a string, despite `1.0` normally being a floating point number.
- YAML Tags provided by this library are lazy (running when the value is request, not load time) unless noted.

### Summary Table

<!--If you are reading this markdown raw with word wrap, this table is not for you. See the list based documentation.-->

|                 Category                 |                                  Tag                                   |           Argument            |                                                                                                   Usage                                                                                                    |
| :--------------------------------------: | :--------------------------------------------------------------------: | :---------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| [**String <br> Formatter**](#formatters) |               [`!Sub`](#tag-Sub)[ⁱ⁺](#interpolates-full)               |             `str`             | `!Sub ${ENVIRONMENT_VARIABLE}` <br> `!Sub ${ENVIRONMENT_VAR:-default value}` <br> `!Sub ${$.JSON.Path.expression}` <br> `!Sub ${/JSON/Pointer/expression}` <br> `!Sub ${&#x24;&#x7B; Escaped HTML &#x7D;}` |
|     [**Manipulator**](#manipulators)     |                           [`!Del`](#tag-Del)                           |             `str`             |                                                                                             `!Del key: value`                                                                                              |
|                                          |                         [`!Merge`](#tag-Merge)                         |     `list[dict \| None]`      |                                                                             `!Merge [{"key1": "value1"}, {"key2": "value2"}]`                                                                              |
|                                          |                   [`!Placeholder`](#tag-Placeholder)                   |             `str`             |                                                                                       `!Placeholder helpful message`                                                                                       |
|                                          |               [`!Ref`](#tag-Ref)[ⁱ⁺](#interpolates-full)               |             `str`             |                                                                    `!Ref $.JSON.Path.expression}` <br> `!Ref /JSON/Pointer/expression`                                                                     |
|          [**Parser**](#parsers)          |                      [`ParseEnv`](#tag-ParseEnv)                       | `str`<br>`\| tuple[str, Any]` |                                                                 `!ParseEnv ENVIRONMENT_VARIABLE` <br> `!ParseEnv ["ENVIRONMENT_VAR", 42]`                                                                  |
|                                          |                  [`ParseEnvSafe`](#tag-ParseEnvSafe)                   | `str`<br>`\| tuple[str, Any]` |                                                             `!ParseEnvSafe ENVIRONMENT_VARIABLE` <br> `!ParseEnvSafe ["ENVIRONMENT_VAR", 42]`                                                              |
|                                          |         [`ParseFile`](#tag-ParseFile)[ⁱ⁺](#interpolates-full)          |             `str`             |                                                                                      `!ParseFile relative/path.yaml`                                                                                       |
|                                          | [`!OptionalParseFile`](#tag-OptionalParseFile)[ⁱ⁺](#interpolates-full) |             `str`             |                                                                                     `!OptionalParseFile optional.yaml`                                                                                     |
|           [**Typer**](#typers)           |            [`!Class`](#tag-Class)[ⁱ](#interpolates-reduced)            |             `str`             |                                                                                             `!Class uuid.UUID`                                                                                             |
|                                          |             [`!Date`](#tag-Date)[ⁱ](#interpolates-reduced)             |             `str`             |                                                                                             `!Date 1988-12-28`                                                                                             |
|                                          |         [`!DateTime`](#tag-DateTime)[ⁱ](#interpolates-reduced)         |             `str`             |                                                                     `!Date 1988-12-28T23:38:00-0600` <br> `!Date 2019-18-17T16:15:14`                                                                      |
|                                          |             [`!Func`](#tag-Func)[ⁱ](#interpolates-reduced)             |             `str`             |                                                                                          `!Func functools.reduce`                                                                                          |
|                                          |             [`!Mask`](#tag-Mask)[ⁱ](#interpolates-reduced)             |             `str`             |                                                                                             `!Mask ${SECRET}`                                                                                              |
|                                          |             [`!UUID`](#tag-UUID)[ⁱ](#interpolates-reduced)             |             `str`             |                                                                                `!UUID 9d7130a6-192f-41e6-88ce-29f0b765be9e`                                                                                |

<a id="interpolates-full"></a>ⁱ⁺: Supports full interpolation syntax of [`!Sub`](#tag-Sub)
<a id="interpolates-reduced"></a>ⁱ: Supports reduced interpolation syntax of [`!Sub`](#tag-Sub) without JSON Path and JSON Pointer syntax.

---

### Formatters

- `!Sub` <a id="tag-Sub"></a>

  - **Argument:** _str_
  - **Usage:**
    ```yaml
    environment_variable: !Sub ${ENVIRONMENT_VARIABLE_THAT_EXISTS}
    with_a_default: !Sub ${ENVIRONMENT_VARIABLE_MIGHT_NOT_EXIST:-some default value}
    with_other_text: !Sub Normal Text + ${ENVIRONMENT_VARIABLE_THAT_EXISTS}
    json_path: !Sub ${$.json.path.expression}
    json_pointer: !Sub ${/json/pointer/expression}
    $: !Sub ${$}
    "${}": !Sub "${&#x24;&#x7B;&#x7D;}"
    ```
  - **Returns:** _str_ ‒ string produced by the interpolation syntax.
  - Interpolations:
    - `${ENVIRONMENT_VARIABLE}`: Replaced with the specified Environment Variable.
      - If the variable does not exist, raises `EnvironmentVaribleNotFound`
    - `${ENVIRONMENT_VARIABLE:-default}`: Replaced with the specified Environment Variable.
      - If variable does not exist, use the text after `:-`.
      - Note: specifier is `:-`.
    - `${ENVIRONMENT_VARIABLE:+<nested_interpolation_spec>}`: Replaced with the specified Environment Variable.
      - If variable does not exist, interpolate the text after `:+`.
      - Note: specifier is `:+`.
    - `${$.json.path.expression}`: Replaced by the object in the configuration specified in JSON Path syntax.
      - Paths must start at full root of configuration, using `$` as the first character.
      - Results:
        - Referencing only strings is recommended. However, paths that return `Mapping` or `Sequence` will be `repr`-ed. Other objects will be `str`-ed.
        - Paths that do not exist raise `JSONPathQueryFailed`.
    - `${/json/pointer/expression}`: Replaced by the object in the configuration specified in JSON Path syntax.
      - Paths must start at full root of configuration, using `/` as the first character.
      - Results:
        - Referencing only strings is recommended. However, paths that return `Mapping` or `Sequence` will be `repr`-ed. Other objects will be `str`-ed.
        - Paths that do not exist raise `JSONPointerQueryFailed`.
    - `${$}`: Replaced with `$`.
      - `!Sub ${$}{}` produces `${}`
    - `${&...;}`: Replaced by the results `html.unescape`.
      - `!Sub ${&#x24;&#x7B;&#x7D;}` produces `${}`
      - `!Sub ${&#x24;&#40;&#41;}` produces `$()`
      - `!Sub ${&#x24;&#91;&#93;}` produces `$[]`
    - Notes:
      - `${...}` is greedy and does not support nesting.
      - Modes other than `:-` and `:+` are reserved and throw `InterpolationSyntaxError`. Use `::` to for escaping colons in environment variable names.
      - `$(...)` and `$[...]` are reserved future for use and will warn with `InterpolationWarning` if used.
      - ⚠️ JSON Path and JSON Pointer can be used to cause infinite loops and/or a `RecursionError`.

- `!Env` <a id="tag-Env"></a>
  - Note: [`!Sub`](#tag-Sub) replaces this functionality and offers more options. `!Env` will not be removed but will not see future updates.
  - **Argument:** _str_.
  - **Usage:**
    ```yaml
    environment_variable: !Env "{{ENVIRONMENT_VARIABLE_THAT_EXISTS}}"
    with_a_default: !Env "{{ENVIRONMENT_VARIABLE_MIGHT_NOT_EXIST:some default value}}"
    ```
  - **Returns:** _str_ ‒ string produced by the string format, replacing `{{VARIABLE_NAME}}` with the Environment Variable specified. Optionally, a default value can be specified should the Environment Variable not exist.

### Manipulators

- `!Del` <a id="tag-Del"></a>
  - **Argument:** _str_.
  - **Usage:**
    ```yaml
    !Del hidden: &common_setting Some Value
    copy1: *common_setting
    copy2: *common_setting
    ```
    _Result:_ `{"copy1: "Some Value", "copy2": "Some Value"}`
  - **Action:** Marks the key and value to be removed just after load (technically: it acts as a part of the load). This allows YAML anchors to be defined in the value and used, but by the time the Configuration is merged and built, the key and value are already removed.
  - Notes:
    - `!Del` will only act when applied to the key of mapped value (`!Del key: value`; not `key: !Del value`). When applied otherwise it does nothing. Using key allows `!Del d: %setting !Func itertools.chain`.
    - `!Del` is one of the few exceptions to laziness and acts at load time.
- `!Merge` <a id="tag-Merge"></a>
  - **Argument:** _list[Any]_.
  - **Usage:**
    ```yaml
    !Merge
    - setting1: some_default_value
    - !ParseFile relative/path/to/file.yaml
    - !OptionalParseFile relative/path/to/optional/file.yaml
    - setting2: some_overriding_value
    ```
  - **Returns:** `Configuration` ‒ Merges are sequence of mapping into a single `Configuration`, filtering out any `Configuration`.
  - Notes:
    - When merging, all objects in the merge list are evaluated. As an explicit example, a [`!ParseFile`](#tag-ParseFile) in the merge list is evaluated with the `!Merge`.
    - Tags in the list merge cannot reference what is being merged.
      - Following is not allowed, because this [`!Ref`](#tag-Ref) acts during the merge:
        ```yaml
        key1: !Merge
          - nested_key:
              settings: values
          - !Ref $.key1.nested_key
        ```
      - Following is allowed, because this [`!Ref`](#tag-Ref) acts after the merge:
        ```yaml
        key1: !Merge
          - nested_key:
              settings: values
          - nested_key2: !Ref $.key1.nested_key
        ```
    - `!Merge` is equivalent to the merge that occurs at Merge Time.
      - The following options result is the same Configuration:
        - `LazyLoadConfiguration("file1.yaml", "file2.yaml")`
          - This is the only option that remains lazy.
        - Loading a file containing:
          ```yaml
          !Merge
          - !OptionalParseFile file1.yaml
          - !OptionalParseFile file2.yaml
          ```
        - `merge(LazyLoadConfiguration("file1.yaml"), LazyLoadConfiguration("file2.yaml"))`
    - The expected use-case for `!Merge` is to be paired with multiple [`!ParseFile`](#tag-ParseFile) and/or [`!OptionalParseFile`](#tag-OptionalParseFile) tags.
- `!Placeholder` <a id="tag-Placeholder"></a>
  - **Argument:** _str_.
  - **Usage:**
    ```yaml
    setting1: !Placeholder message to user
    ```
  - **Action:** `!Placeholder` marks a value as needing to be overridden. If the `!Placeholder` is still present when the value is fetched, a `PlaceholderConfigurationError` is thrown. The exception message includes the attribute name and provided message (e.g. `` !Placeholder at `$.setting1` was not overwritten. Message: "message to user" ``)
  - Note:
    - The `Placeholder` object is created at Load Time. The exception is thrown at Fetch.
- `!Ref` <a id="tag-Ref"></a>
  - **Argument:** _str_.
    - _Supports Full Interpolation Syntax_
  - **Usage:**
    ```yaml
    json_path: !Ref $.json.path.expression
    json_pointer: !Ref /json/pointer/expression
    ```
  - **Returns:** _Any_ ‒ Object referenced in absolute JSON Path or JSON Pointer syntax.
  - Notes:
    - Must begin with either `$` for JSON Path or `/` for JSON Pointer. Otherwise, a `RefMustStartFromRoot` exception is thrown.
    - `!Ref` underlies [`!Sub`](#tag-Sub) reference syntax. `!Ref` returns the object. Whereas [`!Sub`](#tag-Sub) stringifies the objects.
    - JSON Pointer is limited by designed to be a single reference.
    - JSON Path can be used to created objects. `$.*.things` returns a sequence of all values from mappings contain the `things` key. This behavior is not restricted, but not recommended.
      - JSON Path was made available first, because cloud services used a restricted version similarly.
    - ⚠️ `!Ref` can be used to cause infinite loops and/or a `RecursionError`.

### Parsers

- `!ParseEnv` <a id="tag-ParseEnv"></a> and `!ParseEnvSafe` <a id="tag-ParseEnvSafe"></a>
  - **Argument:** _str | tuple[str, Any]_
  - **Usage:**
    ```yaml
    environment_variable_must_exist: !ParseEnv ENVIRONMENT_VARIABLE
    environment_variable_may_exist: !ParseEnv
      - ENVIRONMENT_VARIABLE
      - <YAML object>
    ```
  - **Returns:** _Any_ ‒ specified environment variable parsed.
    - When environment variable does not exist:
      - If argument is `str`, a `EnvironmentVaribleNotFound` error will be thrown.
      - If argument is `tuple`, the second object will be returned.
  - Notes:
    - `!ParseEnvSafe` uses pure YAML loading. `!ParseEnv` uses this library loader.
  - ⚠️ `!ParseEnv` can be used to cause infinite loops and/or a `RecursionError`.
    - `!ParseEnv VAR`, where `VAR='!ParseEnv VAR'`, will loop infinitely.
- `!ParseFile` <a id="tag-ParseFile"></a> and `!OptionalParseFile` <a id="tag-OptionalParseFile"></a>
  - **Argument:** _str_
    - _Supports Full Interpolation Syntax_
  - **Usage:**
    ```yaml
    file_must_exist: !ParseFile relative/path/to/file.yaml
    file_may_exist: !ParseFile relative/path/to/optional/file.yaml
    ```
  - **Returns:** _Any_ ‒ Loads the specified file.
    - When the file does not exist:
      - `!ParseFile` throws `FileNotFoundError`.
      - `!OptionalParseFile` return null (`None`).
  - Notes:
    - `!ParseFile` can be used at the root of the configuration document to act as a file redirect.
    - `!OptionalParseFile` is intended to be used with [`!Merge`](#tag-Merge), where nulls are filtered out.
    - ⚠️ `!ParseFile` and `!OptionalParseFile` can be used to cause infinite loops and/or a `RecursionError`.

### Typers

- `!Class` <a id="tag-Class"></a>
  - **Argument:** _str_
  - **Usage:**
    ```yaml
    class_type: !Class uuid.UUID
    ```
  - **Returns:** `Type` ‒ Imports and returns the specified the class
  - Notes:
    - The current working directory is added prior to importing.
    - Returned object pass `inspect.isclass` test.
- `!Date` <a id="tag-Date"></a>
  - **Argument:** _str_
    - _Supports Reduced Interpolation Syntax_
  - **Usage:**
    ```yaml
    date: !Date 1988-12-28
    ```
  - **Returns:** `date` ‒ Returns the string parsed as ISO 8601 in a python `datetime.date`.
  - Notes:
    - For Python 3.11+, `date.fromisoformat` is used.
    - For Python 3.10, `dateutil.parser.parse(value, yearfirst=True, dayfirst=False).date()` is used.
- `!DateTime` <a id="tag-DateTime"></a>
  - **Argument:** _str_
    - _Supports Reduced Interpolation Syntax_
  - **Usage:**
    ```yaml
    with_timezone: !DateTime "2012-10-31T13:12:09-0600"
    without_timezone: !DateTime "2012-10-31T13:12:09"
    ```
  - **Returns:** `datetime` ‒ Returns the string parsed as ISO 8601 in a python `datetime.datetime`.
  - Notes:
    - For Python 3.11+, `datetime.fromisoformat` is used.
    - For Python 3.10, `dateutil.parser.parse(value, yearfirst=True, dayfirst=False)` is used.
- `!Func` <a id="tag-Func"></a>
  - **Argument:** _str_
    - _Supports Reduced Interpolation Syntax_
  - **Usage:**
    ```yaml
    function: !Func functool.reduce
    ```
  - **Returns:** `Callable` ‒ Imports and returns the specified the function
  - Notes:
    - The current working directory is added prior to importing.
    - Returned object pass `callable` test.
- `!Mask` <a id="tag-Mask"></a>
  - **Argument:** _str_
    - _Supports Reduced Interpolation Syntax_
  - **Usage:**
    ```yaml
    function: !Mask ${SECRET}
    ```
  - **Returns:** `Masked` ‒ the string as a `Masked`
  - Notes:
    - `Masked` inherits from `str`, overwriting the `__repr__` to always be `"'<****>'"`.
    - `Masked` objects are created at Load Time.
    - Some libraries (such as `requests`) explicitly only support `str` and not subclasses of `str`. In those cases, you can `str(masked_value)` to get back the pure `str`.
- `!UUID` <a id="tag-UUID"></a>
  - **Argument:** _str_
    - _Supports Reduced Interpolation Syntax_
  - **Usage:**
    ```yaml
    id: !UUID 9d7130a6-192f-41e6-88ce-29f0b765be9e
    ```
  - **Returns:** `UUID` ‒ the string as a python `uuid.UUID`
