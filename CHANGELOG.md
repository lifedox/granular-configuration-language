# Changelog

<!-- markdownlint-disable-file MD024 -->

## 2.3.0 (next)

- Added `granular_configuration_language.yaml.file_ops` module
- Added `granular_configuration_language.yaml.decorator.eagerio` module

- Added `!EagerParseFile` and `!EagerOptionalParseFile` Tags
- Added Undocumented Tags:
  - `!LoadBindary` and `!EagerLoadBinary` Tag to test binary EagerIO

## 2.2.3

### Fixed

- Boolean expression for the `without_ref` interpolations missing parentheses.
- `!OptionalParseFile` is documented to return `None`. It was returning empty mapping. Changed to result to match documentation.

## 2.2.2

### Added

- Added `needs_root_condition` column to `available_plugins`.
- `G_CONFIG_ENABLE_TAG_TRACKER` to Environment Variables.

### Changed

- Made tag attribute tracking optional via `G_CONFIG_ENABLE_TAG_TRACKER`.
  - `available_plugins` and `available_tags` set `G_CONFIG_ENABLE_TAG_TRACKER` temporarily.
- `!Masked` is now lazy, for consistency with `interpolate_value_without_ref` recommendations.
- Improved documentation.

## 2.2.1

### Changed

- `SafeConfigurationProxy` is now registered as a subclass of `Configuration`.
- Updated many docstrings to improve generated documentation.

## 2.2.0

### Added

- `python -m granular_configuration_language.available_tags` is publicly usable now
- `python -m granular_configuration_language.available_plugins`

### Changed

- Refactored `load_file` and `make_chain_message` to make testing easier

## 2.1.0

### Changed

- `!ParseFile`, `!OptionalParseFile`, and `ParseEnv` will now actively check if there is a loading loop and throw `ParsingTriedToCreateALoop`.
  - Previously, this could result in unexpected behaviors, `RecursionError`, or infinite loops and was not explicitly supported and warned against.

## 2.0.0

### ⚠️ Breaking Changes ⚠️

- YAML Version 1.2 is the default supported version.
  - Reason: Switched from `PyYAML` to `ruamel.yaml`, because `PyYAML` is very dead.
  - `yes/no`, `y/n`, `on/off` is no longer `bool`
  - Octal support is clearer: `010` means 10, `0o10` means 8.
  - Mitigation: YAML 1.1 support can be explicit enabled by using the `%YAML 1.1 ---` directive
- `jsonpath-rw` cannot be installed aside this library.
  - Reason: Switched from `jsonpath-rw` to `python-jsonpath`, because `jsonpath-rw` is very dead.
    - Both `jsonpath-rw` and `python-jsonpath` cannot be installed. `jsonpath-rw` controls `jsonpath_rw` and `jsonpath` modules (despite not explicitly needing the latter). `python-jsonpath` also controls `jsonpath`, but looses in `jsonpath-rw`.
      - `ImportError` occur on the `jsonpath` modules when both are installed.
- `Configuration` no longer fakes being a subclass of `dict`.
  - It remains a `Mapping`.
  - `dict` inheritance was done for compatible with `json.dumps` and other libraries that only support the primitive `dict`, instead of `Mapping`. However, faking the inheritance has always been sketchy and `json.dumps` has failed in rare occurrences.
  - Mitigation: Used one of the following methods:
    - `json.dumps(config.as_dict())`
    - `json.dumps(config, default=granular_configuration_language.json_default)`
    - `config.as_json_string()`
- Configuration is immutable by default now.
  - `Configuration` and `LazyLoadConfiguration` are now immutable mappings.
  - Immutable sequences use `tuple` is used instead of `list`
  - Mitigation: Use `MutableLazyLoadConfiguration` in-place of `LazyLoadConfiguration`.
    - This uses `MutableConfiguration` instead of `Configuration` and `list` for sequences.
    - `MutableConfiguration` is a subclass of `Configuration` and `MutableLazyLoadConfiguration` is a subclass of `LazyLoadConfiguration`, so any `isinstance` check can remain as they were.
    - If you need to dynamically set settings at runtime, `LazyLoadConfiguration` now provides `inject_before` and `inject_after` as immutable way of handling this case.
- Depreciated Features removed:
  - `set_config`/`get_config` pattern
  - INI support
  - Configuration patching
  - `ConfigurationFiles` and `ConfigurationMultiNamedFiles` classes have been removed. `LazyLoadConfiguration` only supports paths (e.g. `pathlib.Path` and `str`).
    - Mitigation: Just use `pathlib.Path` or `str` directly.
- Renamed Exceptions:
  - `ParseEnvError` → `ParseEnvParsingError`
  - `ParseEnvEnvironmentVaribleNotFound` → `EnvironmentVaribleNotFound`
  - `JSONPathQueryMatchFailed` → `JSONPathQueryFailed`
  - `JSONPathMustStartFromRoot` → `RefMustStartFromRoot`
- Previously, YAML Mappings could not override non-Mappings. This has been changed to be more consistent with merge outcomes being "to merge" or "to replace".

### Changed

- Switched from `PyYAML` to `ruamel.yaml`
  - Note: `PyYAML` is very dead
  - This primarily means YAML Version 1.2 is the default supported version.
    - `yes/no`, `y/n`, `on/off` is no longer `bool`
    - Octal support is clearer: `010` means 10, `0o10` means 8.
  - YAML 1.1 support can be explicit enabled by using the `%YAML 1.1 ---` directive
- Switched from `jsonpath-rw` to `python-jsonpath`
  - Note: `jsonpath-rw` is very dead
  - Important: Both `jsonpath-rw` and `python-jsonpath` cannot be installed. `jsonpath-rw` controls `jsonpath_rw` and `jsonpath` modules (despite not explicitly needing the latter). `python-jsonpath` also controls `jsonpath`, but losses in `jsonpath-rw`.
    - `ImportError` occur on the `jsonpath` modules when both are installed.
- Renamed `granular_configuration.yaml_handler` module to `granular_configuration.yaml`
- Configuration no longer fakes being a subclass of `dict`.
  - It remains a `MutableMapping`.
  - `dict` inheritance was done for compatible with `json.dumps` and other library that only support the primitive `dict`, instead of `Mapping`. However, faking the inheritance has always been sketchy and `json.dumps` has failed in rare occurrences.
  - `json_default` is behavior to enable `json.dump` support.
- Previously, YAML Mappings could not override non-Mappings. This has been changed to be more consistent with merge outcomes being "to merge" or "to replace".
- Renamed Exceptions:
  - `ParseEnvError` → `ParseEnvParsingError`
  - `ParseEnvEnvironmentVaribleNotFound` → `EnvironmentVaribleNotFound`
  - `JSONPathQueryMatchFailed` → `JSONPathQueryFailed`
  - `JSONPathMustStartFromRoot` → `RefMustStartFromRoot`
- (_internal detail_) `LazyEval.run()` usage replaced with `LazyEval.result`

### Added

- Add JSON Pointer support where JSON Path is supported.
- Added the following tags:
  - Manipulators: `!Del`, `!Merge`, `!Ref`
  - Parsers: `!ParseEnvSafe`, `ParseFile`, `ParseFileOptional`
  - Typers: `!Date`, `!DateTime`, `!UUID`
    - Note: `python-dateutil` is used for Python 3.10
- Added `Configuration.typed_get`
- Introduced `mutable_configuration` flag, with immutable as default.
  - `Configuration` is no longer a `MutableMapping`, just `Mapping`.
  - `MutableConfiguration` has been added to extend back the `MutableMapping` interface
  - `LazyLoadConfiguration` no longer provides a `MutableMapping` interface, just `Mapping`
  - `MutableLazyLoadConfiguration` has been added to extend back the `MutableMapping` interface and remove needing to cast to `MutableConfiguration`
  - When immutable, `tuple` is used instead of `list`
  - `LazyLoadConfiguration` now provides `inject_before` and `inject_after` as immutable way of dynamically setting settings at runtime.
- Added: JSON Pointer for base_path
- Added Plugin support for adding external Tags
- Added `G_CONFIG_DISABLE_PLUGINS` and `G_CONFIG_DISABLE_TAGS` as supported environment variables to disable select tags.
- Added `merge` to enable multistep configuration loading.
- `Configuration` using `typing.dataclass_transform` to support typed attributes.
  - `Configuration.as_typed` and `LazyLoadConfiguration.as_typed` added enable typing.

### Fixed

- (_internal detail_) Fixed `LazyEval` making copies of `Root`
  - Note: Copying with `LazyEval` still links copies unexpectedly. Now, it is just always connected to the original root (immutability is default now, so only copy immutable configurations).

### Removed

- Removed `set_config` pattern
- Removed INI support
- Completely internalized location logic, removing `ConfigurationFiles`, `ConfigurationMultiNamedFiles`. Just use `pathlib.Path` or `str`.

## 1.8.0

### Changed

- Adds `!Sub` Tag

## 1.5.0

### Changed

- Adds `!ParseEnv` Tag

## 1.4.0

### Changed

- Adds `InvalidBasePathException` as an exception that can be thrown during the load phase of `LazyLoadConfiguration`.
  - This subclasses `KeyError` maintaining compatibility with the state before this exception.
- `LazyLoadConfiguration`'s `base_path` argument now takes a single `str` in addition to the original `typing.Sequence[str]`

## 1.3.1

### Changed

- Adds clear_config

## 1.3

### Changed

- Adds string path support to `LazyLoadConfiguration`
- Adds `set_config`/`get_config` pattern
- Adds `Configuration.patch`

## 1.2

### Changed

- Adding INI support

## 1.1

### Changed

- Adds `!Placeholder` Tag
- Makes tags evaluate lazily (i.e. at first use)
