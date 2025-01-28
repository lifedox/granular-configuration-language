# `granular-configuration-language`

> README is in-progress.

Full documentation at [link](https://lifedox.github.io/granular-configuration-language/index.html)

## Why does this exist?

This library exists to allow your code use YAML as a configuration language for internal and external parties, with added YAML Tags to allow configuration to be crafted from multiple sources.

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
