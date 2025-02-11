# Concepts

## Immutable vs. Mutable

Originally {py:class}`.Configuration` sought to be a drop-in replacement for {py:class}`dict`, so that {py:func}`json.dumps` would just work. This goal has been given up on (as unmaintainable) with version 2.0. With the {py:class}`~collections.abc.MutableMapping` interface of {py:class}`dict` no longer required and cache adding, it was decided that a mutable configuration was dangerous and immutability should be the default.

As such, {py:class}`.Configuration` and {py:class}`.LazyLoadConfiguration` were changed from {py:class}`~collections.abc.MutableMapping` to {py:class}`~collections.abc.Mapping` and loaded YAML sequences from changed from {py:class}`list` to {py:class}`tuple`/{py:class}`~collections.abc.Sequence` by default. Immutability makes them thread-safe, as well.

For compatibility, mutable configuration support was added explicitly, as {py:class}`.MutableConfiguration` and {py:class}`.MutableLazyLoadConfiguration`. In mutable-mode, YAML sequences are loaded as {py:class}`list`/{py:class}`~collections.abc.MutableSequence` and caching is disabled. Modifying a {py:class}`.MutableConfiguration` is not thread-safe. Apart from the added methods of {py:class}`~collections.abc.MutableMapping`, {py:class}`.MutableConfiguration` is identical to {py:class}`.Configuration` and {py:class}`.MutableLazyLoadConfiguration` is identical to {py:class}`.LazyLoadConfiguration`. Any documentation on {py:class}`.Configuration` or {py:class}`.LazyLoadConfiguration` applied to their mutable counterparts.

You should highly consider using the immutable configuration in you code.

---

## Lifecycle

1. **Import Time**: {py:class}`.LazyLoadConfiguration`'s are defined (`CONFIG = LazyLoadConfiguration(...)`).
   - So long as the next step does not occur, all identical immutable configurations<sup>\*</sup> identified and marked for caching.
     - Loading a configuration clears the cache for all identical immutable configurations, meaning if another identical immutable configuration is created, it will be loaded separately.
2. **First Fetch**: Configuration is fetched for the first time (through `CONFIG.value`, `CONFIG[value]`, `CONFIG.config`, and such)
   1. **Load Time**:
      1. The file system is scanned for specified configuration files.
      2. Each file is read and parsed.
   2. **Merge Time**:
      - Any Tags defined at the root of the file are run (i.e. the file beginning with a tag: `!Parsefile ...` or `!Merge ...`).
      - The loaded Configurations are merged in-order into one Configuration.
        - Any files that do not define a Mapping are filtered out.
        - Mappings are merged recursively. Any non-mapping overrides. Newer values override older values. (See [more](#merging))
          - `{"a": "b": 1}` + `{"a: {"b": {"c": 1}}` ⇒ `{"a: {"b": {"c": 1}}`
          - `{"a: {"b": {"c": 1}}` + `{"a: {"b": {"c": 2}}` ⇒ `{"a: {"b": {"c": 2}}`
          - `{"a: {"b": {"c": 2}}` + `{"a: {"b": {"d": 3}}` ⇒ `{"a: {"b": {"c": 2, "d": 3}}`
          - `{"a: {"b": {"c": 2, "d": 3}}` + `{"a": "b": 1}` ⇒ `{"a": "b": 1}`
   3. **Build Time**:
      1. The Base Path is applied.
      2. The Base Paths for any {py:class}`.LazyLoadConfiguration` shared this identical immutable configuration is applied.
         - Exceptions that occur (such as {py:class}`.InvalidBasePathException`) are stored, so they emit for the first fetch of the associated {py:class}`.LazyLoadConfiguration`.
      3. {py:class}`.LazyLoadConfiguration` no longer holds a reference to the root object. If no tags depend on the root Configuration, it will be free (`!Ref` is an example of a tag that holds a reference to the root Configuration until it is run).
         - If an exception occurs, the root Configuration is unavoidable caught in the frame.
3. **Fetching a Lazy Tag**:
   1. Upon first get of the {py:class}`.LazyEval` object, the underlying function is called.
   2. The result replaces the {py:class}`.LazyEval` in the Configuration, so the {py:class}`.LazyEval` runs exactly once.

When making copies, it is important to note that {py:class}`.LazyEval` do not copy (they return themselves). This is to aid in running exactly once and prevent cycles with the root reference.

This means that a deep copy of a {py:class}`.Configuration` can share state with the original, if any {py:class}`.LazyEval` is present. Using immutable {py:class}`.Configuration` (and {py:class}`.LazyLoadConfiguration`) will prevent needing to make copies. {py:meth}`~.Configuration.as_dict()` is also a great way to make a mutable copy.

<sup>\*</sup> "identical immutable configurations" means using {py:class}`.LazyLoadConfiguration` with the same set of possible input files, and not using `inject_after` or `inject_before`.

---

## Merging

Merging is the heart of this library. With it, you gain the ability to have settings defined in multiple possible locations and the ability to override settings based on a consistent pattern.

Merging is explicitly exposed through {py:class}`.LazyLoadConfiguration`, [`!Merge`](yaml.md#merge), and {py:func}`.merge` (see [Load Boundary Limitations](#load-boundary-limitations) for an important note).

### Describing Priority

#### As a sentence

> Mappings are merged, and everything else is replaced, with last-in winning.

#### As a table with code

| From <br> `First-in.yaml` | From <br> `Next-in.yaml` | Outcome                             |
| :-----------------------: | :----------------------: | ----------------------------------- |
|           Value           |            \*            | Next-in **replaces** First-in       |
|          Scalar           |            \*            | Next-in **replaces** First-in       |
|         Sequence          |            \*            | Next-in **replaces** First-in       |
|          Mapping          |          Value           | Next-in **replaces** First-in       |
|          Mapping          |          Scalar          | Next-in **replaces** First-in       |
|          Mapping          |         Sequence         | Next-in **replaces** First-in       |
|          Mapping          |         Mapping          | Next-in is **merged** into First-in |

Code:

```python
CONFIG = LazyLoadConfiguration("First-in.yaml", "Next-in.yaml")
CONFIG = merge("First-in.yaml", "Next-in.yaml")
CONFIG = LazyLoadConfiguration("merge.yaml")
```

```yaml
# merge.yaml
!Merge
- !ParseFile First-in.yaml
- !ParseFile Next-in.yaml
```

#### As Explicit Examples

````{list-table}
:header-rows: 1
:align: center

* - First-in
  - \+
  - Next-in
  - ⇒
  - Result
* - ```yaml
    a:
      b: 1
    ```
  - \+
  - ```yaml
    a:
      b:
        c: 1
    ```
  - ⇒
  - ```yaml
    a:
      b:
        c: 1
    ```
* - ```yaml
    a:
      b:
        c: 1
    ```
  - \+
  - ```yaml
    a:
      b:
        c: 2
    ```
  - ⇒
  - ```yaml
    a:
      b:
        c: 2
    ```
* - ```yaml
    a:
      b:
        c: 2
    ```
  - \+
  - ```yaml
    a:
      b:
        d: 3
    ```
  - ⇒
  - ```yaml
    a:
      b:
        c: 2
        d: 3
    ```
* - ```yaml
    a:
      b:
        c: 2
        d: 3
    ```
  - \+
  - ```yaml
    a:
      b: 1
    ```
  - ⇒
  - ```yaml
    a:
      b: 1
    ```
````

---

## JSON Path/Pointer, `!Ref`, & Root

[`!Ref`](yaml.md#ref) and [`!Sub`](yaml.md#sub) have the concept of querying other sections of your configuration for values. This was added as a request to make for deployment configuration simpler.

Cases discussed included:

- Using `env_location_var_name` from {py:class}`.LazyLoadConfiguration`, you would define environment-specific files. Then use the environment variable to select the associated file and a common config would pull strings from environment config to reduce copy-and-paste related problem.

  ```yaml
  # config.yaml
  common_base_path:
    settings:
      setting1: !Sub ${$.common_base_path.lookup.environment.name} is cool
  ```

  ```yaml
  # dev.yaml
  common_base_path:
    lookup:
      environment:
        name: dev
  ```

  ```yaml
  # test.yaml
  common_base_path:
    lookup:
      environment:
        name: test
  ```

  ```python
  # Getting the deployed setting
  LazyLoadConfiguration(
      "config.yaml",
      base_path="/common_base_path/settings",
      env_location_var_name="CONFIG_LOCATION"
  ).config.setting1
  ```

- Using `!Ref` to select environment settings from a mapping of environment.

  ```yaml
  # config.yaml
  common_base_path:
    all_setting:
      dev:
        setting1: dev is cool
      test:
        setting1: test is cooler
    settings: !Ref /common_base_path/all_setting/${ENVIRONMENT_NAME}
  ```

  ```python
  # Getting the deployed setting
  LazyLoadConfiguration(
      "config.yaml",
      base_path="/common_base_path/settings"
  ).config.setting1
  ```

In order to not create a doubly-linked structure or lose `base_path` ability to dereference settings that are fenced out, it was decided to use root-orient syntax.

**"Root"** refers the configuration output after the Merge Time step, **before** `base_path` is applied. Within your configuration, you must explicitly include your `base_path` when querying.

JSON Path was selected as the syntax for being an open standard (and familiarity). JSON Pointer was added when `python-jsonpath` was selected as the JSON Path implementation, because it is ready supported. JSON Pointer is the more correct choice, as it can only be a reference.

> Note: If you explore the code or need to [add a custom tag](plugins.md#adding-custom-tags), {py:class}`.Root` and {py:class}`.RootType` represent Root as a type. {py:class}`.LazyRoot` is used during Build Time to allow the delayed reference of Root after it has been created.

<!-- markdownlint-disable MD012 -->

> Memory Note: `base_path` will remove a reference count toward Root, but any Tag needing Root will hold a reference until evaluated. [`!Sub`](yaml.md#sub) checks if it needs Root before holding a reference.

### Load Boundary Limitations

A load boundary is created by Root. You cannot query outside the Root and every load event is an independent Root.

In more concrete terms, every {py:class}`.LazyLoadConfiguration` has an independent Root.

Where this matter is merging configuration. [`!ParseFile`](yaml.md#parsefile--optionalparsefile) passes the Root it whatever it loads, so [`!Merge`](yaml.md#merge) does not introduce Load Boundaries.

However, {py:func}`.merge` does introduce Load Boundaries.

#### Working with an example

We have three files in `ASSET_DIR / "ref_cannot_cross_loading_boundary/"`

````{list-table}
:header-rows: 0
:align: center

* - ```yaml
    # 1.yaml
    test:
      1: !Ref /ref
    ref: I came from 1.yaml
    ```
  - ```yaml
    # 2.yaml
    test:
      2: !Ref /ref
    ref: I came from 2.yaml
    ```
  - ```yaml
    # 3.yaml
    test:
      3: !Ref /ref
    ref: I came from 3.yaml
    ```
````

```python
files = (
    ASSET_DIR / "ref_cannot_cross_loading_boundary/1.yaml",
    ASSET_DIR / "ref_cannot_cross_loading_boundary/2.yaml",
    ASSET_DIR / "ref_cannot_cross_loading_boundary/3.yaml",
)

# Merging three separate `LazyLoadConfiguration` instances
config = merge(files)

assert config.as_dict() == {
    "test": {
        1: "I came from 1.yaml",
        2: "I came from 2.yaml",
        3: "I came from 3.yaml",
    },
    "ref": "I came from 3.yaml",
}

# One `LazyLoadConfiguration` merging three files
config = LazyLoadConfiguration(*files).config

assert config.as_dict() == {
    "test": {
        1: "I came from 3.yaml",
        2: "I came from 3.yaml",
        3: "I came from 3.yaml",
    },
    "ref": "I came from 3.yaml",
}
```

In the {py:func}`.merge` case, merging work as expected. However, the three `!Ref /ref` ended up reference three different Roots.

In the {py:class}`.LazyLoadConfiguration` case, the three `!Ref /ref` reference the same Root, as it generally desired.

For completeness’ sake, merging with [`!Merge`](yaml.md#merge) has the same result as the {py:class}`.LazyLoadConfiguration` case.

```yaml
# ref_cannot_cross_loading_boundary.yaml
!Merge
- !ParseFile ref_cannot_cross_loading_boundary/1.yaml
- !ParseFile ref_cannot_cross_loading_boundary/2.yaml
- !ParseFile ref_cannot_cross_loading_boundary/3.yaml
```
