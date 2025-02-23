# Configuration Options for Tags

<!-- markdownlint-disable-file MD024 -->

## Environment Variables

The following environment variables are used as configuration for this library:

- `G_CONFIG_DISABLE_PLUGINS`
  - **Input:** Comma-delimited list of plugin names
  - **Description:** Disables tags provided by the selected plugins.
  - Use [`available_plugins`](#viewing-available-plugins) to view plugins
  - Internal tags cannot be disabled as a plugin.
- `G_CONFIG_DISABLE_TAGS`
  - **Input:** Comma-delimited list of tag names
  - **Description:** Disables the selected tags.
  - Use [`available_tags`](#viewing-available-tags) to view plugins
  - Tag names start with `!`

## Helper Scripts

(available_tags)=

### Viewing Available Tags

This script prints the available tags and the properties in each tag.

This script is affected by [`G_CONFIG_DISABLE_PLUGINS`](#environment-variables) and [`G_CONFIG_DISABLE_TAGS`](#environment-variables).

#### Command

```shell
python -m granular_configuration_language.available_tags
```

#### Options

- `csv`: Output is formatted as a csv table.
  - Default, if `table` is not available.
- `json`: Output is JSON-mapping.
- `table`: Output is pretty table.
  - Requires `tabulate` to be available. Default, if available.

#### Usage

```text
usage: available_tags.py [-h] [{csv,json,table}]

Shows available tags

positional arguments:
  {csv,json,table}

options:
  -h, --help  show this help message and exit

The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies
```

When `tabulate` is installed, the default option is `table`, otherwise `csv`.

**Example install:**

```shell
pip install 'granular-configuration-language[printing]'
```

#### Headers

- `category`: Category of the Tag
- `tag`: Name of the Tag
- `type`: Argument type
  - Value comes from {py:meth}`TagDecoratorBase.user_friendly_type <granular_configuration_language.yaml.decorators.TagDecoratorBase.user_friendly_type>`.
- `interpolates`: Specifies if the tags interpolates
  - `full` - Tags uses {py:func}`.interpolate_value_with_ref`
  - `reduced` - Tags uses {py:func}`.interpolate_value_without_ref`
- `lazy` - Specifies if the tags is lazy.
  - `NOT_LAZY` - Tags uses {py:func}`.as_not_lazy`
- `returns` - Type annotation of the return of function that implements that Tag

#### Sample Output (using `table` mode)

```text
category     tag                 type                   interpolates    lazy      returns
-----------  ------------------  ---------------------  --------------  --------  -------------
Formatter    !Env                str                                              str
Formatter    !Sub                str                    full                      str
Manipulator  !Del                str                                    NOT_LAZY  str
Manipulator  !Merge              list[Any]                                        Configuration
Manipulator  !Placeholder        str                                    NOT_LAZY  Placeholder
Manipulator  !Ref                str                    full                      str
Parser       !ParseEnv           str | tuple[str, Any]                            Any
Parser       !ParseEnvSafe       str | tuple[str, Any]                            Any
Parser       !ParseFile          str                    full                      Any
Parser       !OptionalParseFile  str                    full                      Any
Typer        !Class              str                    reduced                   Callable
Typer        !Date               str                    reduced                   date
Typer        !DateTime           str                    reduced                   date
Typer        !Func               str                    reduced                   Callable
Typer        !Mask               str                    reduced         NOT_LAZY  Masked
Typer        !UUID               str                    reduced                   UUID
Undoc-ed     !Dict               dict[Any, Any]                                   dict
```

(available_plugins)=

### Viewing Available Plugins

This script prints the available plugins, what tags are included with the plugins, and where the implementation of the Tag is.

This script is affected by [`G_CONFIG_DISABLE_PLUGINS`](#environment-variables) and [`G_CONFIG_DISABLE_TAGS`](#environment-variables).

#### Command

```shell
python -m granular_configuration_language.available_plugins
```

#### Options

- `csv`: Output is formatted as a csv table.
  - Default, if `table` is not available.
- `json`: Output is JSON-mapping.
- `table`: Output is pretty table.
  - Requires `tabulate` to be available. Default, if available.

#### Usage

```text
usage: available_plugins.py [-h] [{csv,json,table}]

Shows available plugins

positional arguments:
  {csv,json,table}

options:
  -h, --help        show this help message and exit

The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies
```

When `tabulate` is installed, the default option is `table`, otherwise `csv`.

**Example install:**

```shell
pip install 'granular-configuration-language[printing]'
```

#### Headers

- `plugin`: Plugin name
  - `<gcl-built-in>` represents internal tags
- `category`: Category of the Tag
- `tag`: Tag Name
- `handler`: function that implements that Tag.

#### Sample Output (using `table` mode)

```text
plugin          category     tag                 handler
--------------  -----------  ------------------  -----------------------------------------------------------------------
<gcl-built-in>  Formatter    !Env                granular_configuration_language.yaml._tags._env.handler
<gcl-built-in>  Formatter    !Sub                granular_configuration_language.yaml._tags._sub.handler
<gcl-built-in>  Manipulator  !Del                granular_configuration_language.yaml._tags._del.handler
<gcl-built-in>  Manipulator  !Merge              granular_configuration_language.yaml._tags._merge.handler
<gcl-built-in>  Manipulator  !Placeholder        granular_configuration_language.yaml._tags._placeholder.handler
<gcl-built-in>  Manipulator  !Ref                granular_configuration_language.yaml._tags._ref.handler
<gcl-built-in>  Parser       !ParseEnv           granular_configuration_language.yaml._tags._parse_env.handler
<gcl-built-in>  Parser       !ParseEnvSafe       granular_configuration_language.yaml._tags._parse_env.handler_safe
<gcl-built-in>  Parser       !ParseFile          granular_configuration_language.yaml._tags._parse_file.handler
<gcl-built-in>  Parser       !OptionalParseFile  granular_configuration_language.yaml._tags._parse_file.handler_optional
<gcl-built-in>  Typer        !Date               granular_configuration_language.yaml._tags._date.date_handler
<gcl-built-in>  Typer        !DateTime           granular_configuration_language.yaml._tags._date.datetime_handler
<gcl-built-in>  Typer        !Mask               granular_configuration_language.yaml._tags._mask.handler
<gcl-built-in>  Typer        !UUID               granular_configuration_language.yaml._tags._uuid.handler
<gcl-built-in>  Undoc-ed     !Dict               granular_configuration_language.yaml._tags._dict.handler
official_extra  Typer        !Class              granular_configuration_language.yaml._tags.func_and_class.class_handler
official_extra  Typer        !Func               granular_configuration_language.yaml._tags.func_and_class.func_handler
```
