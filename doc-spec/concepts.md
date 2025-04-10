# Concepts

## Immutable vs. Mutable

Originally {py:class}`.Configuration` sought to be a drop-in replacement for {py:class}`dict`, so that {py:func}`json.dumps` would just work. This goal has been given up on (as unmaintainable) with version 2.0. With the {py:class}`~collections.abc.MutableMapping` interface of {py:class}`dict` no longer required and in order to add caching, it was decided that a mutable configuration was dangerous and immutability should be the default.

As such, {py:class}`.Configuration` and {py:class}`.LazyLoadConfiguration` were changed from {py:class}`~collections.abc.MutableMapping` to {py:class}`~collections.abc.Mapping` and loaded YAML sequences from changed from {py:class}`list` to {py:class}`tuple`/{py:class}`~collections.abc.Sequence` by default. Immutability makes them thread-safe, as well.

For compatibility, mutable configuration support was added explicitly, as {py:class}`.MutableConfiguration` and {py:class}`.MutableLazyLoadConfiguration`, both just adding {py:class}`~collections.abc.MutableMapping`. In mutable-mode, YAML sequences are loaded as {py:class}`list`/{py:class}`~collections.abc.MutableSequence` and caching is disabled. Modifying a {py:class}`.MutableConfiguration` is not thread-safe. Documentation will reference {py:class}`.Configuration` or {py:class}`.LazyLoadConfiguration`, but all concepts apply to their mutable counterparts, unless noted in the [Code Specification](spec)

You should highly consider using the immutable configuration in you code.

---

## Lifecycle

<sup>\*</sup> "identical immutable configurations" means using {py:class}`.LazyLoadConfiguration` with the same set of possible input files, and not using `inject_after` or `inject_before`.

1. **Import Time**: {py:class}`.LazyLoadConfiguration`'s are defined (`CONFIG = LazyLoadConfiguration(...)`).
   - So long as the next step does not occur, all "identical immutable configurations"<sup>\*</sup> are marked as using the same configuration cache.
     - Loading a configuration clears its marks from the cache, meaning if another identical immutable configuration is created, it will be loaded separately.
2. **First Fetch**: Configuration is fetched for the first time (through `CONFIG.value`, `CONFIG["value"]`, `CONFIG.config`, and such)
   1. **Load Time**:
      1. The file system is scanned for specified configuration files.
         - Paths are expanded ({py:meth}`~pathlib.Path.expanduser`) and resolved ({py:meth}`~pathlib.Path.resolve`) at Import Time, but checked for existence and read during Load Time.
      2. Each file that exists is read and loaded.
   2. **Merge Time**:
      1. Any Tags defined at the root of the file are run (i.e. the file beginning with a tag: `!Parsefile ...` or `!Merge ...`).
      2. The loaded {py:class}`.Configuration` instances are merged in-order into one {py:class}`.Configuration`.
         - Any files that do not define a {py:class}`~collections.abc.Mapping` are filtered out.
           - `"str"` is valid YAML, but not a {py:class}`~collections.abc.Mapping`.
           - Everything being filtered out results in an empty {py:class}`.Configuration`.
         - Mappings are merged recursively. Any non-mapping overrides. Newer values override older values. (See [Merging](#merging) for more)
           - `{"a": "b": 1}` + `{"a: {"b": {"c": 1}}` ⇒ `{"a: {"b": {"c": 1}}`
           - `{"a: {"b": {"c": 1}}` + `{"a: {"b": {"c": 2}}` ⇒ `{"a: {"b": {"c": 2}}`
           - `{"a: {"b": {"c": 2}}` + `{"a: {"b": {"d": 3}}` ⇒ `{"a: {"b": {"c": 2, "d": 3}}`
           - `{"a: {"b": {"c": 2, "d": 3}}` + `{"a": "b": 1}` ⇒ `{"a": "b": 1}`
   3. **Build Time**:
      1. The Base Path is applied.
      2. The Base Paths for any {py:class}`.LazyLoadConfiguration` that shared this identical immutable configuration are applied.
         - Exceptions that occur (such as {py:class}`.InvalidBasePathException`) are stored, so they emit for the first fetch of the associated {py:class}`.LazyLoadConfiguration`.
      3. {py:class}`.LazyLoadConfiguration` no longer holds a reference to the Root configuration (see [Root](#json-pathpointer-ref--root) for a more detailed definition).
         - If no tags depend on the Root, it will be freed.
           - [`!Ref`](yaml.md#ref) is an example of a tag that holds a reference to the Root until it is run.
         - If an exception occurs, the Root is unavoidable caught in the frame.
3. **Fetching a Lazy Tag**:
   1. Upon first get of the {py:class}`.LazyEval` object, the underlying function is called.
   2. The result replaces the {py:class}`.LazyEval` in the Configuration, so the {py:class}`.LazyEval` runs exactly once.

---

## Making Copies

When making copies, it is important to note that {py:class}`.LazyEval` instance do not copy with either {py:func}`~copy.copy` or {py:func}`~copy.deepcopy` (they return themselves). This is to aid in running exactly once, prevent deep copies of Root leading to branches might never run their {py:class}`.LazyEval` instances, and unexpected memory use.

This means that a {py:func}`~copy.deepcopy` of a {py:class}`.Configuration` or {py:class}`.MutableConfiguration` instance can share state with the original, if any {py:class}`.LazyEval` is present, despite that breaking the definition of a deep copy.

```{admonition} Mitigation
:class: tip

- Using immutable {py:class}`.Configuration` (and {py:class}`.LazyLoadConfiguration`) will prevent needing to make copies.
- {py:meth}`~.Configuration.as_dict()` is also a great way to make a safe mutable copy.
- {py:meth}`~.MutableConfiguration.evaluate_all()` will run all {py:class}`.LazyEval` instance, making a {py:class}`.MutableConfiguration` instance safe to copy.
```

---

## Merging

Merging is the heart of this library. With it, you gain the ability to have settings defined in multiple possible locations and the ability to override settings based on a consistent pattern.

See [Merge Equivalency](#merge-equivalency) for examples using merge.

### Describing Priority

#### As a sentence

> Mappings are merged, and everything else is replaced, with last-in winning.

#### As a table with code

:::{list-table}
:header-rows: 1
:align: center
:width: 80%

- - <div align="center"> From <code class="docutils literal notranslate">First-in.yaml</code></div>
  - <div align="center"> From <code class="docutils literal notranslate">Next-in.yaml</code></div>
  - Outcome
- - <div align="center"> Value</div>
  - <div align="center"> *</div>
  - Next-in **replaces** First-in
- - <div align="center"> Scalar</div>
  - <div align="center"> *</div>
  - Next-in **replaces** First-in
- - <div align="center"> Sequence</div>
  - <div align="center"> *</div>
  - Next-in **replaces** First-in
- - <div align="center"> Mapping</div>
  - <div align="center"> Value</div>
  - Next-in **replaces** First-in
- - <div align="center"> Mapping</div>
  - <div align="center"> Scalar</div>
  - Next-in **replaces** First-in
- - <div align="center"> Mapping</div>
  - <div align="center"> Sequence</div>
  - Next-in **replaces** First-in
- - <div align="center"> Mapping</div>
  - <div align="center"> Mapping</div>
  - Next-in is **merged** into First-in

:::

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
:width: 60%
:widths: 4 1 4 1 4

* - <div align="center">First-in</div>
  - <div align="center">+</div>
  - <div align="center">Next-in</div>
  - <div align="center">⇒</div>
  - <div align="center">Result</div>
* - ```yaml
    a:
      b: 1
    ```
  - <div align="center">+</div>
  - ```yaml
    a:
      b:
        c: 1
    ```
  - <div align="center">⇒</div>
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
  - <div align="center">+</div>
  - ```yaml
    a:
      b:
        c: 2
    ```
  - <div align="center">⇒</div>
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
  - <div align="center">+</div>
  - ```yaml
    a:
      b:
        d: 3
    ```
  - <div align="center">⇒</div>
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
  - <div align="center">+</div>
  - ```yaml
    a:
      b: 1
    ```
  - <div align="center">⇒</div>
  - ```yaml
    a:
      b: 1
    ```
````

### Merge Equivalency

The following options result is the same Configuration:

:::{list-table}
:header-rows: 1
:width: 100%

- - Case
  - Notes
- - ```python
    CONFIG = LazyLoadConfiguration(
        "file1.yaml",
        "file2.yaml",
    )
    ```
  - {py:class}`.LazyLoadConfiguration`
    - `"file1.yaml"` and `"file2.yaml"` are read during the "Load Time" of the "First Fetch".
    - The merge occurs as a part of the "Merge Time" merge.
    - Best option.
- - ```python
    CONFIG = LazyLoadConfiguration(
        "merged.yaml",
    )
    ```
    ```yaml
    # merged.yaml
    !Merge
    - !OptionalParseFile file1.yaml
    - !OptionalParseFile file2.yaml
    ```
  - [`!Merge`](yaml.md#merge)
    - `"file1.yaml"` and `"file2.yaml"` are read during the "Load Time" of the "First Fetch".
    - The merged occurs before the "Merge Time" merge.
      - The [`!Merge`](yaml.md#merge) must be evaluated fully, in order to be merged into the final configuration.
    - This is less efficient than merging with {py:class}`.LazyLoadConfiguration`.
- - ```python
    CONFIG = merge(
        "file1.yaml",
        "file2.yaml"
    )
    ```
  - {py:func}`.merge`
    - `"file1.yaml"` and `"file2.yaml"` are read immediately.
    - `"file1.yaml"` and `"file2.yaml"` are loaded as separate {py:class}`.LazyLoadConfiguration` with individual Load Boundaries.
    - This is far less efficient than merging with {py:class}`.LazyLoadConfiguration`
    - Exists for merging a framework configuration with a library-specific configuration.
      - The explicit case was for a `pytest` sub-plugin that was a part of a framework plugin.
      - Using {py:func}`.merge` allows users to set settings in the framework configuration without requiring
        the framework configuration needing to know about the sub-plugin.

:::

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

```{admonition} About Types
:class: note

If you explore the code or need to [add a custom tag](plugins.md#adding-custom-tags), {py:class}`.Root` and {py:class}`.RootType` represent Root as a type. {py:class}`.LazyRoot` is used during Build Time to allow delayed reference of Root until after it has been created.
```

```{admonition} About Memory
:class: note

`base_path` will remove a reference count toward Root, but any Tag needing Root will hold a reference until evaluated. [`!Sub`](yaml.md#sub) checks if it needs Root before holding a reference.
```

(load-boundary-limitations)=

### Load Boundary Limitations

A load boundary is created by Root. You cannot query outside the Root and every load event is an independent Root.

In more concrete terms, every {py:class}`.LazyLoadConfiguration` has an independent Root.

Where this matter is merging configuration. [`!ParseFile`](yaml.md#parsefile--optionalparsefile) passes the Root to whatever it loads, so [`!Merge`](yaml.md#merge) does not introduce Load Boundaries.

However, {py:func}`.merge` does introduce Load Boundaries.

#### Working with an example

We have the following three files in `ASSET_DIR / "ref_cannot_cross_loading_boundary/"`

````{list-table}
:header-rows: 0
:width: 100%
:widths: 1 1 1

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

With the following code:

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

<br>

In the {py:func}`.merge` case, merging works as expected. However, the three `!Ref /ref` ended up referencing three different Roots.

In the {py:class}`.LazyLoadConfiguration` case, the three `!Ref /ref` reference the same Root, as is generally desired.

For completeness’ sake, merging with [`!Merge`](yaml.md#merge) has the same result as the {py:class}`.LazyLoadConfiguration` case.

```yaml
# ref_cannot_cross_loading_boundary.yaml
!Merge
- !ParseFile ref_cannot_cross_loading_boundary/1.yaml
- !ParseFile ref_cannot_cross_loading_boundary/2.yaml
- !ParseFile ref_cannot_cross_loading_boundary/3.yaml
```

---

## Loading Loops

Because [`!ParseFile`](yaml.md#parsefile--optionalparsefile), [`!OptionalParseFile`](yaml.md#parsefile--optionalparsefile), and [`!ParseEnv`](yaml.md#parseenv--parseenvsafe) load data from an external source (i.e. files and environment variables), they introduce the risk of circularly loading these sources.

```{note}

[`!ParseEnvSafe`](yaml.md#parseenv--parseenvsafe) does not include support for tags, so it does not have this risk, as it can only ever be an end to the chain.
```

In order to prevent looping, each load of a file or environment is tracked **per chain**, and a {py:class}`.ParsingTriedToCreateALoop` exception is thrown just before a previously loaded (in chain) source tries to load.

This does not prevent the same source load being loaded more than once if it is multiple chains.

### Example of Multiple Chains

**Environment:**

```shell
VAR=!ParseFile 2.yaml
```

**Configuration:**

````{list-table}
:header-rows: 0
:align: left
:width: 66%
:widths: 1 1

* - ```yaml
    # 1.yaml
    chain1: !ParseEnv VAR
    chain2: !ParseEnv VAR
    ```
  - ```yaml
    # 2.yaml
    key: value
    ```
````

**Code:**

```python
CONFIG = LoadLazyConfiguration("1.yaml")

assert CONFIG.chain1.key == "value"  # 1.yaml→#VAR→2.yaml
assert CONFIG.chain2.key == "value"  # 1.yaml→#VAR→2.yaml
```

Sources `$VAR` and `2.yaml` are loaded twice. Once for `CONFIG.chain1` and once for `CONFIG.chain2`.

_(Note: Using `!Ref chain1` for `chain2` would have prevented the second load)_

### Looping Example with Environment Variables

The following is an example of a catastrophic loop, using [`!ParseEnv`](yaml.md#parseenv--parseenvsafe)

**Environment:**

```shell
VAR1=!ParseEnv VAR2
VAR2=!ParseEnv VAR3
VAR3=!ParseEnv VAR1
```

**Configuration:**

```yaml
# config.yaml
setting1: !ParseEnv VAR1
```

**Code:**

```python
CONFIG = LoadLazyConfiguration("config.yaml")

CONFIG.setting1 # Would cause an infinite loop without detection.
                # Note: This is not recursion, because a new LazyEval
                #       instance is created every load.
                #       You would be waiting to run out of memory or stack.
```

### Looping Example with Files

The following is an example of a loop, using [`!ParseFile`](yaml.md#parsefile--optionalparsefile):

**Configuration:**

````{list-table}
:header-rows: 0
:width: 100%
:widths: 1 1 1

* - ```yaml
    # 1.yaml
    safe: 1.yaml
    next: !ParseFile 2.yaml
    ```
  - ```yaml
    # 2.yaml
    safe: 2.yaml
    next: !ParseFile 3.yaml
    ```
  - ```yaml
    # 3.yaml
    safe: 3.yaml
    next: !ParseFile 1.yaml
    ```
````

**Code:**

```python
CONFIG = LoadLazyConfiguration("1.yaml")

CONFIG.safe           # "1.yaml"
CONFIG.next.safe      # "2.yaml"
CONFIG.next.next.safe # "3.yaml"
CONFIG.next.next.next # Would load `1.yaml` again without detection.

# Without detection, `.next` could be appended endlessly
CONFIG.next.next.next                # 1.yaml→2.yaml→3.yaml→1.yaml
CONFIG.next.next.next.next           # 1.yaml→2.yaml→3.yaml→1.yaml→2.yaml
CONFIG.next.next.next.next.next      # 1.yaml→2.yaml→3.yaml→1.yaml→2.yaml→3.yaml
CONFIG.next.next.next.next.next.next # 1.yaml→2.yaml→3.yaml→1.yaml→2.yaml→3.yaml→1.yaml
```
