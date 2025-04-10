# Configuration Options for Tags

<!-- markdownlint-disable-file MD024 -->

## Environment Variables

The following environment variables are used as configuration for this library:

- User Configuration Options:
  - `G_CONFIG_DISABLE_PLUGINS`
    - **Input:** Comma-delimited list of plugin names.
    - **Description:** Disables tags provided by the selected plugins.
    - Use `python -m granular_configuration_language.available_plugins` to [view](#viewing-available-plugins) plugins.
    - Internal tags cannot be disabled as a plugin.
  - `G_CONFIG_DISABLE_TAGS`
    - **Input:** Comma-delimited list of tag names.
    - **Description:** Disables the selected tags.
    - Use `python -m granular_configuration_language.available_tags` to [view](#viewing-available-tags) tags.
    - Tag names start with `!`.
- Internally used variables (Documented as courtesy; not for users to use):
  - `G_CONFIG_ENABLE_TAG_TRACKER`
    - **Input:** `TRUE`
    - **Description:** Enables tag property tracking.
    - Automatically set while [`available_plugins`](#viewing-available-plugins) and [`available_tags`](#viewing-available-tags) run.
    - _Added_: 2.2.2
    - _Removed_: 2.3.0 -- {py:func}`.with_tag` required a better framework for tracking tag attributes.
  - `G_CONFIG_FORCE_CAN_TABLE_FALSE`
    - **Input:** `TRUE`
    - **Description:** Used to test `table` not being available for [`available_plugins`](#viewing-available-plugins) and [`available_tags`](#viewing-available-tags).
    - _Added_: 2.3.0

## Helper Scripts

(available_tags)=

### Viewing Available Tags

This script prints the available tags and the properties in each tag.

This script is affected by [`G_CONFIG_DISABLE_PLUGINS`](#environment-variables) and [`G_CONFIG_DISABLE_TAGS`](#environment-variables).

#### Command

```shell
python -m granular_configuration_language.available_tags
```
<br>

#### Options

- Positional:
  - _Mode_:
    - `csv`: Output is formatted as a CSV table.
      - Default, if `table` is not available.
    - `json`: Output is JSON-mapping.
    - `table`: Output is pretty table.
      - Requires [tabulate](https://pypi.org/project/tabulate/) to be available. Default, if available.
      - Use a terminal width of at least 120 characters for best viewing.

#### Usage

```text
usage: available_tags.py [-h] [{csv,json,table}]

Shows available tags

positional arguments:
  {csv,json,table}  Mode, default={table}

options:
  -h, --help        show this help message and exit

The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies
```

When [tabulate](https://pypi.org/project/tabulate/) is installed, the default option is `table`, otherwise `csv`.

**Example install:**

```shell
pip install 'granular-configuration-language[printing]'
```
<br>

#### Headers

- `category`: Category of the Tag.
  - Value comes from {py:meth}`.TagDecoratorBase.__init__`→`category`.
- `tag`: Name of the Tag
  - Value comes from {py:meth}`.TagDecoratorBase.__init__`→`tag`.
- `type`: Argument type of the Tag.
  - Value comes from {py:meth}`TagDecoratorBase.user_friendly_type <granular_configuration_language.yaml.decorators.TagDecoratorBase.user_friendly_type>`.
- `interpolates`: Specifies if the tags interpolates.
  - `full` - Tags uses {py:func}`.interpolate_value_with_ref`.
  - `reduced` - Tags uses {py:func}`.interpolate_value_without_ref`.
- `lazy` - Specifies if the tags are lazy.
  - `NOT_LAZY` - Tags uses {py:func}`.as_not_lazy`.
  - `EAGER_IO` - Tags uses {py:func}`.as_eager_io` or {py:func}`.as_eager_io_with_root_and_load_options`.
    - _Added_: 2.3.0
- `returns` - Type annotation of the return of function that implements the Tag.
- `eio_inner_type` - EagerIO inner type.
  - This is the type the function that implements the Tag takes and the type the EagerIO Preprocessor returns.
  - Value comes from the type annotation of the return of the EagerIO Preprocessor.
  - Only applicable to EagerIO Tags.
  - _Added_: 2.3.0

#### Sample Output (using `table` mode)

```text
category     tag                      type                   interpolates    lazy      returns        eio_inner_type
-----------  -----------------------  ---------------------  --------------  --------  -------------  -----------------
Formatter    !Env                     str                                              str
Formatter    !Sub                     str                    full                      str
Manipulator  !Del                     str                                    NOT_LAZY  str
Manipulator  !Merge                   list[Any]                                        Configuration
Manipulator  !Placeholder             str                                    NOT_LAZY  Placeholder
Manipulator  !Ref                     str                    full                      Any
Parser       !ParseEnv                str | tuple[str, Any]                            Any
Parser       !ParseEnvSafe            str | tuple[str, Any]                            Any
Parser       !ParseFile               str                    full                      Any
Parser       !OptionalParseFile       str                    full                      Any
Parser       !EagerParseFile          str                    reduced         EAGER_IO  Any            EagerIOTextFile
Parser       !EagerOptionalParseFile  str                    reduced         EAGER_IO  Any            EagerIOTextFile
Typer        !Class                   str                    reduced                   Callable
Typer        !Date                    str                    reduced                   date
Typer        !DateTime                str                    reduced                   date
Typer        !Func                    str                    reduced                   Callable
Typer        !Mask                    str                    reduced                   Masked
Typer        !UUID                    str                    reduced                   UUID
Undoc-ed     !Dict                    dict[Any, Any]                                   dict
Undoc-ed     !EagerLoadBinary         str                    reduced         EAGER_IO  bytes          EagerIOBinaryFile
Undoc-ed     !LoadBinary              str                    reduced                   bytes
```

(available_plugins)=

### Viewing Available Plugins

This script prints the available plugins, what tags are included with the plugins, and where the implementation of the Tag is.

This script is affected by [`G_CONFIG_DISABLE_PLUGINS`](#environment-variables) and [`G_CONFIG_DISABLE_TAGS`](#environment-variables).

#### Command

```shell
python -m granular_configuration_language.available_plugins
```
<br>

#### Options

- Positional:
  - _Mode_:
    - `csv`: Output is formatted as a CSV table.
      - Default, if `table` is not available.
    - `json`: Output is JSON-mapping.
    - `table`: Output is pretty table.
      - Requires [tabulate](https://pypi.org/project/tabulate/) to be available. Default, if available.
      - Use a terminal width of at least 120 characters for best viewing.
- Flags:
  - `--long`, `-l`: Use long names in table instead of short names.
    - Requires [tabulate](https://pypi.org/project/tabulate/) to be available.
    - _Added_: 2.3.0

#### Usage

```text
usage: available_plugins.py [-h] [--long] [{csv,json,table}]

Shows available plugins

positional arguments:
  {csv,json,table}  Mode, default={table}

options:
  -h, --help        show this help message and exit
  --long, -l        In "table" mode, use long names.
                    "Shortenings" lookup will not print.

The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies
```

When [tabulate](https://pypi.org/project/tabulate/) is installed, the default option is `table`, otherwise `csv`.

**Example install:**

```shell
pip install 'granular-configuration-language[printing]'
```
<br>

#### Headers

- `plugin`: Name of Plugin.
  - Value comes from `[project.entry-points."granular_configuration_language_20_tag"]`.
  - `<gcl-built-in>` represents internal tags.
- `category`: Category of the Tag.
  - Value comes from {py:meth}`.TagDecoratorBase.__init__`→`category`.
- `tag`: Name of the Tag.
  - Value comes from {py:meth}`.TagDecoratorBase.__init__`→`tag`.
- `handler`: Function that implements the Tag.
- `needs_root_condition`: Name of the "needs_root_condition" function.
  - Comes from {py:func}`.as_lazy_with_root`
  - _Added_: 2.2.2
- `eager_io`: Name of the EagerIO Preprocessor.
  - Comes from the input to {py:func}`.as_eager_io` or {py:func}`.as_eager_io_with_root_and_load_options`
  - _Added_: 2.3.0

#### Sample Output (using `table` mode)

```text
plugin          category     tag                      handler                      needs_root_condition    eager_io
--------------  -----------  -----------------------  ---------------------------  ----------------------  ------------
<gcl-built-in>  Formatter    !Env                     <gcl>._env.tag
<gcl-built-in>  Formatter    !Sub                     <gcl>._sub.tag               ntrpl_needs_ref
<gcl-built-in>  Manipulator  !Del                     <gcl>._del.tag
<gcl-built-in>  Manipulator  !Merge                   <gcl>._merge.tag
<gcl-built-in>  Manipulator  !Placeholder             <gcl>._placeholder.tag
<gcl-built-in>  Manipulator  !Ref                     <gcl>._ref.tag
<gcl-built-in>  Parser       !ParseEnv                <gcl>._parse_env.tag
<gcl-built-in>  Parser       !ParseEnvSafe            <gcl>._parse_env.safe
<gcl-built-in>  Parser       !ParseFile               <gcl>._parse_file.tag
<gcl-built-in>  Parser       !OptionalParseFile       <gcl>._parse_file.opt
<gcl-built-in>  Parser       !EagerParseFile          <gcl>._eager_parse_file.tag                          text_ntrpl
<gcl-built-in>  Parser       !EagerOptionalParseFile  <gcl>._eager_parse_file.opt                          text_ntrpl
<gcl-built-in>  Typer        !Date                    <gcl>._date.date_
<gcl-built-in>  Typer        !DateTime                <gcl>._date.datetime_
<gcl-built-in>  Typer        !Mask                    <gcl>._mask.tag
<gcl-built-in>  Typer        !UUID                    <gcl>._uuid.tag
<gcl-built-in>  Undoc-ed     !Dict                    <gcl>._dict.tag
<gcl-built-in>  Undoc-ed     !EagerLoadBinary         <gcl>._load_binary.eager_                            binary_ntrpl
<gcl-built-in>  Undoc-ed     !LoadBinary              <gcl>._load_binary.tag
official_extra  Typer        !Class                   <gcl>.func_and_class.class_
official_extra  Typer        !Func                    <gcl>.func_and_class.func_

Shortenings:
`<gcl>` = `granular_configuration_language.yaml._tags`
`binary_ntrpl` = `eager_io_binary_loader_interpolates`
`ntrpl_needs_ref` = `interpolation_needs_ref_condition`
`text_ntrpl` = `eager_io_text_loader_interpolates`
```
