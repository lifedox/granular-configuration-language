# `granular-configuration-language`

[![Coverage badge](https://raw.githubusercontent.com/lifedox/granular-configuration-language/python-coverage-comment-action-data/badge.svg)](https://github.com/lifedox/granular-configuration-language/tree/python-coverage-comment-action-data) ![Testing workflow](https://github.com/lifedox/granular-configuration-language/actions/workflows/testing.yaml/badge.svg?event=push) ![codeql workflow](https://github.com/lifedox/granular-configuration-language/actions/workflows/codeql-analysis.yaml/badge.svg?event=push)

> ⚠️ **This library is meant for trusted configuration files only.** ⚠️

Get started or read more at the [documentation site](https://lifedox.github.io/granular-configuration-language/doc-spec/getting_started.html).

## Why does this exist?

This library exists to allow your code use YAML as a configuration language for internal and external parties, with added [YAML Tags](https://lifedox.github.io/granular-configuration-language/doc-spec/yaml.html) to allow configuration to be crafted from multiple sources.

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
        log_to: !Sub file://var/log/${$.app.log_as}.log
      ```
- You are writing a [`pytest`](https://docs.pytest.org/en/stable/) plugin that create test data using named fixtures configured by the user.
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

## Why the long name?

- It's "granular" because you can specify settings across multiple files at a fine granularity for overriding values.
- It is meant for trusted "configuration" files.
- Including "language" make it clear that this is not the source of configuration.
  - A valid piece of feedback was that it sounded like it was the source for configuration, not the processing of generic configuration files.
  - "Format" sounded weirder than "language".
