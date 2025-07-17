# YAML Tags

<!-- markdownlint-disable-file MD051 -->

- **Argument** and **Return** use Python primitive type as common reference.
  - To convert to YAML node definitions:
    - {py:data}`~typing.Any` is any type.
    - {py:class}`str` is "scalar"
    - {py:class}`list` is "sequence"
    - {py:class}`tuple` is a sized "sequence"
    - {py:class}`dict` is "mapping"
      - All "mapping" mapping nodes return as a {py:class}`.Configuration`.
        - Or {py:class}`.MutableConfiguration`, when using {py:class}`.MutableLazyLoadConfiguration`.
  - Tags in YAML only support "scalar", "sequence", and "mapping".
    - As such,`!Tag 1.0` is always a string, despite `1.0` normally being a floating point number.
- YAML Tags provided by this library are lazy (running when the value is request, not load time) unless noted.
- YAML Tags that are lazy do not support being used as keys to mappings.

## Summary Table

<!-- Non-breaking space on "Tag" Header forces horzontal scrollbar to be appear before tags become unreadable on a narrow view -->

````{list-table}
:header-rows: 1
:width: 100%

* - Category
  - Tag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  - Argument
  - Usage
* - [**Formatters**](#formatters)
  - [`!Sub`](#sub) [{sup}`i+`](#interpolates-full){.abbr title="Supports full interpolation syntax"}
  - `str`
  - `!Sub ${ENVIRONMENT_VARIABLE}` <br>
    `!Sub ${ENVIRONMENT_VAR:-default value}` <br>
    `!Sub Normal Text + ${ENVIRONMENT_VAR}` <br>
    `!Sub ${/JSON/Pointer/expression}` <br>
    `!Sub ${$.JSON.Path.expression}` <br>
    `!Sub ${$}` <br>
    `!Sub ${&#x24;&#x7B; Escaped HTML &#x7D;}`
* - [**Manipulators**](#manipulators)
  -  [`!Del`](#del)
  - `str`
  - `!Del key: value`
* -
  - [`!Merge`](#merge)
  - `list[dict|None]`
  - ```
    !Merge
    - key1: value1
    - key2: value2
    ```
* -
  - [`!Placeholder`](#placeholder)
  - `str`
  - `!Placeholder helpful message`
* -
  - [`!Ref`](#ref) [{sup}`i+`](#interpolates-full){.abbr title="Supports full interpolation syntax"}
  - `str`
  - `!Ref /JSON/Pointer/expression` <br>
    `!Ref $.JSON.Path.expression`
* - [**Parsers**](#parsers)
  - [`!ParseEnv`](#parseenv--parseenvsafe)
  - `str |` <br>
    `tuple[str,Any]`
  - `!ParseEnv ENVIRONMENT_VARIABLE` <br>
    `!ParseEnv ["ENVIRONMENT_VAR", 42]`
* -
  - [`!ParseEnvSafe`](#parseenv--parseenvsafe)
  - `str |` <br>
    `tuple[str,Any]`
  - `!ParseEnvSafe ENVIRONMENT_VARIABLE` <br>
    `!ParseEnvSafe ["ENVIRONMENT_VAR", 42]`
* -
  - [`!ParseFile`](#parsefile--optionalparsefile) [{sup}`i+`](#interpolates-full){.abbr title="Supports full interpolation syntax"}
  - `str`
  - `!ParseFile relative/path.yaml`
* -
  - [`!OptionalParseFile`](#parsefile--optionalparsefile) [{sup}`i+`](#interpolates-full){.abbr title="Supports full interpolation syntax"}
  - `str`
  - `!OptionalParseFile optional.yaml`
* - [**Typers**](#typers)
  - [`!Class`](#class) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!Class uuid.UUID`
* -
  - [`!Date`](#date) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!Date 1988-12-28`
* -
  - [`!DateTime`](#datetime) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!Date 1988-12-28T23:38:00-0600` <br>
    `!Date 2019-18-17T16:15:14`
* -
  - [`!Func`](#func) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!Func functools.reduce`
* -
  - [`!Mask`](#mask) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!Mask ${SECRET}`
* -
  - [`!UUID`](#uuid) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!UUID 9d7130a6-{...}-29f0b765be9e`
````

## EagerIO Tag Table

See [EagerIO documentation](eagerio.md#) for more details on EagerIO.

:::{list-table}
:header-rows: 1
:width: 100%

- - Category
  - Tag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  - Argument
  - Usage
- - [**Parsers**](#parsers)
  - [`!EagerParseFile`](#parsefile--optionalparsefile) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!EagerParseFile relative/path.yaml`
- -
  - [`!EagerOptionalParseFile`](#parsefile--optionalparsefile) [{sup}`i-`](#interpolates-reduced){.abbr title="Supports reduced interpolation syntax (without JSON Path or JSON Pointer syntax)"}
  - `str`
  - `!EagerOptionalParseFile optional.yaml`

:::

&nbsp;

[{sup}`i+`]{#interpolates-full} : Supports full interpolation syntax of [`!Sub`](#sub).
<br><!--Looks good in GitHub-->
[{sup}`i-`]{#interpolates-reduced} : Supports reduced interpolation syntax of [`!Sub`](#sub) without JSON Path or JSON Pointer syntax.

---

## Formatters

(tag-sub)=

### `!Sub`

```yaml
environment_variable: !Sub ${ENVIRONMENT_VARIABLE_THAT_EXISTS}
with_a_default: !Sub ${ENVIRONMENT_VARIABLE_MIGHT_NOT_EXIST:-some default value}
with_other_text: !Sub Normal Text + ${ENVIRONMENT_VARIABLE_THAT_EXISTS}
json_pointer: !Sub ${/json/pointer/expression}
json_path: !Sub ${$.json.path.expression}
$: !Sub ${$}
"${}": !Sub ${&#x24;&#x7B;&#x7D;}
```

- **Argument:** _str_
- **Returns:** {py:class}`str` ‒ string produced by the interpolation syntax.
- [Interpolations]{#interpolations}:
  - `${ENVIRONMENT_VARIABLE}`: Replaced with the specified Environment Variable.
    - If the variable does not exist, raises {py:class}`.EnvironmentVaribleNotFound`
    - Use `::` to escape colons in environment variable names.
  - `${ENVIRONMENT_VARIABLE:-default}`: Replaced with the specified Environment Variable.
    - If variable does not exist, use the text after `:-`.
    - Note: specifier is `:-`.
  - `${ENVIRONMENT_VARIABLE:+<nested_interpolation_spec>}`: Replaced with the specified Environment Variable.
    - If variable does not exist, use the text after `:+` to interpolate a result.
    - Note: specifier is `:+`.
  - `${/json/pointer/expression}`: Replaced by the object in the configuration specified in JSON Pointer syntax.
    - Paths must start at full root of the configuration, using `/` as the first character.
    - Results:
      - Referencing strings is recommended.
        - Paths that return a {py:class}`~collections.abc.Mapping` or {py:class}`~collections.abc.Sequence` will be {py:func}`repr`-ed.
        - Other objects will be {py:class}`str`-ed.
      - Paths that do not exist raise {py:class}`.JSONPointerQueryFailed`.
  - `${$.json.path.expression}`: Replaced by the object in the configuration specified in JSON Path syntax.
    - Paths must start at full root of the configuration, using `$` as the first character.
    - JSON Pointer is recommended over JSON Path.
    - JSON Path syntax includes the ability to construct objects. While allowed, it is not recommended behavior.
    - Results:
      - Referencing strings is recommended.
        - Paths that return a {py:class}`~collections.abc.Mapping` or {py:class}`~collections.abc.Sequence` will be {py:func}`repr`-ed.
        - Other objects will be {py:class}`str`-ed.
      - Paths that do not exist raise {py:class}`.JSONPathQueryFailed`.
  - `${$}`: Replaced with `$`.
    - `!Sub ${$}{}` produces `${}`
  - `${&...;}`: Replaced by the results of {py:func}`html.unescape`.
    - `!Sub ${&#x24;&#x7B;&#x7D;}` produces `${}`
    - `!Sub ${&#x24;&#40;&#41;}` produces `$()`
    - `!Sub ${&#x24;&#91;&#93;}` produces `$[]`
  - Reserved Syntax:
    - Modes other than `:-` and `:+` are reserved and throw {py:class}`.InterpolationSyntaxError`.
      - Use `::` to escape colons in environment variable names.
    - `$(...)` is reserved future for use and will warn with {py:class}`.InterpolationWarning` if used.
- Notes:
  - `${...}` is greedy and does not support nesting (i.e. `!Sub ${${}}` sees `${` as the inner expression).
  - `!Sub` checks if there is an JSON Path or JSON Pointer expression before keeping a reference to the root of the configuration.

```{admonition} Recursion Possible
:class: caution
**Example:** Loading `a: !Sub ${$.a}` will throw {py:class}`RecursionError`, when `CONFIG.a` is called.
```

---

### `!Env`

```yaml
environment_variable: !Env "{{ENVIRONMENT_VARIABLE_THAT_EXISTS}}"
with_a_default: !Env "{{ENVIRONMENT_VARIABLE_MIGHT_NOT_EXIST:some default value}}"
```

- **Argument:** _str_.
- **Returns:** {py:class}`str` ‒ string produced by the string format, replacing `{{VARIABLE_NAME}}` with the Environment Variable specified. Optionally, a default value can be specified should the Environment Variable not exist.
- Notes:
  - Does not support environment variables with colons.

```{admonition} Deprecated
:class: note
[`!Sub`](#sub) replaces this functionality and offers more options. `!Env` will not be removed but will not see future updates.
```

---

&nbsp;

## Manipulators

### `!Del`

```yaml
!Del hidden: &common_setting Some Value
copy1: *common_setting
copy2: *common_setting
# Loads as: {"copy1": "Some Value", "copy2": "Some Value"}

!Del setting_with_tag: &user_id !UUID 83e3c814-2cdf-4fe6-b703-89b0a379759e
user: *user_id
# Loads as: {"user": UUID("83e3c814-2cdf-4fe6-b703-89b0a379759e")}
# `&user_id !UUID` and `!UUID &user_id` worked the same.
```

- **Argument:** _str_.
- **Action:** Marks the key and value to be removed just after load.
  - This allows YAML anchors to be defined in the value and used elsewhere is the file, but by the time the configuration is merged and built, the key and value are already removed.
  - _Technically: This acts as a part of the load, not explicitly afterward._
- Notes:
  - `!Del` will only act when applied to the key of mapping pair.
    - Works: `!Del key: value`
    - Does nothing: `key: !Del value`.
  - `!Del` is an exception to laziness and acts at load time.

---

### `!Merge`

```yaml
!Merge
- setting1: some_default_value
- !ParseFile relative/path/to/file.yaml
- !OptionalParseFile relative/path/to/optional/file.yaml
- setting2: some_overriding_value
```

- **Argument:** _list[Any]_.
- **Returns:** {py:class}`.Configuration` ‒ The merged {py:class}`.Configuration` from the sequence of mappings, filtering out any non-mapping entries.
  - When merging with {py:class}`.MutableLazyLoadConfiguration`, the return type is {py:class}`.MutableConfiguration`.
- Notes:
  - For more details about merging see [Merging](concepts.md#merging).
  - The expected use-case for `!Merge` is to be paired with multiple [`!ParseFile`](#parsefile--optionalparsefile)and/or [`!OptionalParseFile`](#parsefile--optionalparsefile) tags.
  - When merging, all objects in the merge list are evaluated.
    - From the example, both the [`!ParseFile`](#parsefile--optionalparsefile) and [`!OptionalParseFile`](#parsefile--optionalparsefile) entries are evaluated with `!Merge`, not after `!Merge`.
  - If every item is filtered out, the result is an empty {py:class}`.Configuration`.

::: {caution}

Tags in the sequence argument cannot reference what is being merged.
:::

:::{admonition} Following is not allowed, because this [`!Ref`](#ref) acts during the merge:
:class: danger
:collapsible: closed

```yaml
key1: !Merge
  - nested_key:
      settings: values
  - !Ref $.key1.nested_key
```

:::

:::{admonition} Following is allowed, because this [`!Ref`](#ref) acts after the merge:
:class: tip
:collapsible: closed

```yaml
key1: !Merge
  - nested_key:
      settings: values
  - nested_key2: !Ref $.key1.nested_key
```

:::

---

(tag-placeholder)=

### `!Placeholder`

```yaml
setting1: !Placeholder message to user
```

- **Argument:** _str_.
- **Action:** `!Placeholder` marks a value as needing to be overridden.
  - If the `!Placeholder` is still present when the value is fetched, a {py:class}`.PlaceholderConfigurationError` is thrown. The exception message includes the attribute name and provided message (e.g. `` !Placeholder at `$.setting1` was not overwritten. Message: "message to user" ``)
- Note:
  - The {py:class}`.Placeholder` object is created at Load Time. The exception is thrown when Fetched.
  - {py:class}`.PlaceholderConfigurationError` is thrown by the {py:class}`.Configuration` class. `!Placeholder` as a scalar or sequence will just return a {py:class}`.Placeholder` instance.

---

### `!Ref`

```yaml
json_pointer: !Ref /json/pointer/expression
json_path: !Ref $.json.path.expression
```

- **Argument:** _str_.
  - _Supports Full Interpolation [Syntax](#interpolations)_
- **Returns:** {py:data}`~typing.Any` ‒ Object referenced in absolute JSON Path or JSON Pointer syntax.
- Notes:
  - Must begin with either `$` for JSON Path or `/` for JSON Pointer. Otherwise, a {py:class}`.RefMustStartFromRoot` exception is thrown.
  - JSON Pointer is recommended over JSON Path.
  - `!Ref` underlies [`!Sub`](#sub)'s reference interpolation syntax. `!Ref` returns the object. Whereas [`!Sub`](#sub) stringifies the object.
  - JSON Pointer is limited by designed to be a single reference.
  - JSON Path can be used to created objects. `$.*.things` returns a sequence of all values from mappings contain the `things` key.
    - This behavior is not restricted, but not recommended.
    - JSON Path was made available first, because cloud services used a restricted version similarly.

```{admonition} Recursion Possible
:class: caution
**Example:** Loading `a: !Ref /a` will throw {py:class}`RecursionError`, when `CONFIG.a` is called.
```

---

&nbsp;

## Parsers

### `!ParseEnv` | `ParseEnvSafe`

```yaml
environment_variable_must_exist: !ParseEnv ENVIRONMENT_VARIABLE
environment_variable_may_exist: !ParseEnv
  - ENVIRONMENT_VARIABLE
  - <YAML object>
single_line_example: !ParseEnv [ENV_VAR, false]
```

- **Argument:** _str | tuple[str, Any]_
- **Returns:** {py:data}`~typing.Any` ‒ Result of parsing the specified environment variable.
  - When environment variable does not exist:
    - If argument is {py:class}`str`, a {py:class}`.EnvironmentVaribleNotFound` error will be thrown.
    - If argument is {py:class}`tuple`, the second object will be returned.
- Notes:
  - `!ParseEnvSafe` uses a pure safe YAML loader. `!ParseEnv` uses this library's loader.
  - This was created to make Boolean environment variables more consistent.
    - For `value: !ParseEnvSafe [ENV_VAR, false]`:
      - If `ENV_VAR=TRUE`, `Config.value` is {py:data}`True`.
      - If `ENV_VAR=FALSE`, `Config.value` is {py:data}`False`.
      - If `ENV_VAR` is not set, `Config.value` is {py:data}`False`.
      - Using [`!Sub`](#sub), `FALSE` would need to be an empty string (`""`), which is less obvious than `FALSE`.
  - _(Since 2.1.0)_ `!ParseEnv` detects loading loops and throws {py:class}`.ParsingTriedToCreateALoop` when trying to load an environment variable already part of the chain.
    - See [Loading Loops](concepts.md#loading-loops) for an explanation with examples.

---

### `!ParseFile` | `!OptionalParseFile`

```yaml
file_must_exist: !ParseFile relative/path/to/file.yaml
file_may_exist: !ParseFile relative/path/to/optional/file.yaml
```

- **Argument:** _str_
  - _Supports Full Interpolation [Syntax](#interpolations)_
- **Returns:** {py:data}`~typing.Any` ‒ Result of loading the specified file.
  - When the file does not exist:
    - `!ParseFile` throws {py:class}`FileNotFoundError`.
    - `!OptionalParseFile` return null ({py:data}`None`).
- Notes:
  - `!ParseFile` can be used at the root of the configuration document to act as a file redirect.
  - `!OptionalParseFile` is intended to be used with [`!Merge`](#merge), where nulls are filtered out.
  - _(Since 2.1.0)_ `!ParseFile` detects file loading loops and throws {py:class}`.ParsingTriedToCreateALoop` when trying to load a file already part of the chain.
    - See [Loading Loops](concepts.md#loading-loops) for an explanation with examples.
- EagerIO Versions:
  - `!EagerParsefile` and `!EagerOptionalParseFile` work the same as their original counterparts.
    - Files are read at Load Time and parsed at Fetch Time.
      - Because of this, EagerIO Tags only support the _Reduced Interpolation [Syntax](#interpolations)_.
      - _Added_: 2.3.0

---

&nbsp;

## Typers

### `!Class`

```yaml
class_type: !Class uuid.UUID
```

- **Argument:** _str_
  - _Supports Reduced Interpolation [Syntax](#interpolations)_
- **Returns:** {py:class}`type` ‒ Specified the class.
- Throws:
  - {py:class}`.DoesNotExist`: if the class does not exist.
  - {py:class}`.IsNotAClass`: if the class is not callable.
- Notes:
  - The current working directory is added prior to importing the specified module.
  - Returned object must pass {py:func}`inspect.isclass` as {py:data}`True`.

---

### `!Date`

```yaml
date: !Date 1988-12-28
```

- **Argument:** _str_
  - _Supports Reduced Interpolation [Syntax](#interpolations)_
- **Returns:** {py:class}`~datetime.date` ‒ String parsed as ISO 8601 in a Python {py:class}`datetime.date`.
- Notes:
  - For Python 3.11+, {py:meth}`date.fromisoformat() <datetime.date.fromisoformat>` is used.
  - For Python 3.10, `dateutil.parser.parse(value, yearfirst=True, dayfirst=False).date()` is used.

---

### `!DateTime`

```yaml
with_time_zone: !DateTime "2012-10-31T13:12:09-0600"
without_time_zone: !DateTime "2012-10-31T13:12:09"
```

- **Argument:** _str_
  - _Supports Reduced Interpolation [Syntax](#interpolations)_
- **Returns:** {py:class}`~datetime.datetime` ‒ String parsed as ISO 8601 in a Python {py:class}`datetime.datetime`.
- Notes:
  - For Python 3.11+, {py:meth}`datetime.fromisoformat() <datetime.datetime.fromisoformat>` is used.
  - For Python 3.10, `dateutil.parser.parse(value, yearfirst=True, dayfirst=False)` is used.

---

### `!Func`

```yaml
function: !Func functools.reduce
```

- **Argument:** _str_
  - _Supports Reduced Interpolation [Syntax](#interpolations)_
- **Returns:** {py:class}`~collections.abc.Callable` ‒ Specified function.
- Throws:
  - {py:class}`.DoesNotExist`: if the function does not exist.
  - {py:class}`.IsNotCallable`: if the function is not callable.
- Notes:
  - The current working directory is added prior to importing the specified module.
  - Returned object must pass {py:func}`callable` as {py:data}`True`.

---

(tag-mask)=

### `!Mask`

```yaml
function: !Mask ${SECRET}
```

- **Argument:** _str_
  - _Supports Reduced Interpolation [Syntax](#interpolations)_
- **Returns:** {py:class}`.Masked` ‒ The string as a {py:class}`.Masked`
- Notes:
  - {py:class}`.Masked` inherits from {py:class}`str`, with the {py:meth}`~object.__repr__` overridden to always return the same constant literal `'<****>'`.
  - Some libraries (such as [requests](https://requests.readthedocs.io/en/latest/)) explicitly only support {py:class}`str` and not subclasses of {py:class}`str`.
    - In those cases, you can `str(masked_value)` to get back the pure {py:class}`str`.

---

### `!UUID`

```yaml
id: !UUID 9d7130a6-192f-41e6-88ce-29f0b765be9e
```

- **Argument:** _str_
  - _Supports Reduced Interpolation [Syntax](#interpolations)_
- **Returns:** {py:class}`~uuid.UUID` ‒ The string parsed by Python {py:class}`uuid.UUID`,
