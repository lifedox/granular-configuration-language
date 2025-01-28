# Conceptions

## Immutable vs. Mutable

Originally {py:class}`.Configuration` sought to be a drop-in replacement for {py:class}`dict`, so that {py:func}`json.dumps` would just work. This goal has been given up on (as unmaintainable) with version 2.0. With the {py:class}`~collections.abc.MutableMapping` interface of {py:class}`dict` no longer required and cache adding, it was decided that a mutable configuration was dangerous and immutability should be the default.

As such, {py:class}`.Configuration` and {py:class}`.LazyLoadConfiguration` were changed from {py:class}`~collections.abc.MutableMapping` to {py:class}`~collections.abc.Mapping` and loaded YAML sequences from changed from {py:class}`list` to {py:class}`tuple`/{py:class}`~collections.abc.Sequence` by default. Immutability makes them thread-safe, as well.

For compatibility, mutable configuration support was added explicitly, as {py:class}`.MutableConfiguration` and {py:class}`.MutableLazyLoadConfiguration`. In mutable-mode, YAML sequences are loaded as {py:class}`list`/{py:class}`~collections.abc.MutableSequence` and caching is disabled. Modifying a {py:class}`.MutableConfiguration` is not thread-safe. Apart from the added methods of {py:class}`~collections.abc.MutableMapping`, {py:class}`.MutableConfiguration` is identical to {py:class}`.Configuration` and {py:class}`.MutableLazyLoadConfiguration` is identical to {py:class}`.LazyLoadConfiguration`. Any documentation on {py:class}`.Configuration` or {py:class}`.LazyLoadConfiguration` applied to their mutable counterparts.

---

## Lifecycle

1. **Import Time**: {py:class}`.LazyLoadConfiguration`'s are defined (`CONFIG = LazyLoadConfiguration(...)`).
   - So long as the next step does not occur, all identical immutable configurations identified and marked for caching.
     - Loading a configuration clears the cache for all identical immutable configurations, meaning if another identical immutable configuration is created, it will be loaded separately.
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
      2. The Base Paths for any {py:class}`.LazyLoadConfiguration` shared this identical immutable configuration is applied.
         - Exceptions that occur (such as {py:class}`.InvalidBasePathException`) are stored, so they emit for the first fetch of the associated {py:class}`.LazyLoadConfiguration`.
      3. {py:class}`.LazyLoadConfiguration` no longer holds a reference to the root object. If no tags depend on the root Configuration, it will be free (`!Ref` is an example of a tag that holds a reference to the root Configuration until it is run).
         - If an exception occurs, the root Configuration is unavoidable caught in the frame.
3. **Fetching a Lazy Tag**:
   1. Upon first get of the {py:class}`.LazyEval` object, the underlying function is called.
   2. The result replaces the {py:class}`.LazyEval` in the Configuration, so the {py:class}`.LazyEval` run exactly once.

When making copies, it is important to note that {py:class}`.LazyEval` do not copy (they return themselves). This is to aid in running exactly once and prevent cycles with the root reference.

This means that a deep copy of a {py:class}`.Configuration` can share state with the original, if any {py:class}`.LazyEval` is present. Using immutable {py:class}`.Configuration` (and {py:class}`.MutableConfiguration`) will prevent needing to make copies. {py:meth}`~.Configuration.as_dict()` is also a great way to make a mutable copy.
