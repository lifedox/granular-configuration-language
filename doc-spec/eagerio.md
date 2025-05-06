# Avoiding IO blocking when using `asyncio` (EagerIO)

:::{admonition} Philosophical Thought Process
:class: note
:collapsible: closed

{py:mod}`asyncio` is an important tool for concurrency, and EagerIO is the result of the thought experiment of question: "Is there anything that make the user experience better for {py:mod}`asyncio`?"

While this library's interface is highly compatible with async code, since most of it is straightforward getting objects out of mappings. There are some places where blocking code does exist.

Namely:

- The initial load of configuration.
- Any Tags that use IO.
- Any Tags that are CPU-intensive

I believe it is allowable to ignore the CPU-bound case. No Tag is inherently complex (users are in control) and the GIL exists. That leaves two categories for IO-bound cases.

---

Starting with IO-bound Tags, the biggest thing to bear in mind is that tags are optional, most tags act on in memory data (environment variables and configuration data), and all tags run-once and are cached immediately afterward.

The first thought was to make {py:class}`~collections.abc.Awaitable` proxy for {py:meth}`~object.__getattr__` calls. It would maximum the opportunities for coroutines to run and enables the few IO-bound Tags to run waiting. But most all the time, the wrapper would exist to immediately return a primitive. The `await` would just be chained overhead. Typing would be annoying or back to just using {py:data}`~typing.Any`. Realistically, the most optimal version would be an async {py:func}`~operator.attrgetter`-like method (Reminder: {py:func}`~operator.attrgetter` requires type checker to implement special behavior).

So, instead of using {py:mod}`asyncio` that leaves meeting {py:mod}`asyncio` in the middle. Since we cannot `await`, and we want coroutines to avoid waiting for IO, what if we ran that IO-bound work ahead of time---like async would---, so when a coroutine requests data, the IO is probably already loaded (This put the "eager" in **Eager**IO.).

The only challenge is when to run the IO of the EagerIO Tags. It needs to be compatible with synchronous and asynchronous code, able to handle users not doing a step, and libraries. In the end, the simplest, most maintainable option was to start the IO at load time, so there was no behavioral or interface change. User opts into EagerIO by using an EagerIO Tag.

---

That leaves the question of the initial load. With not using `await` for Tags, the same solution of pushing IO into threads is the direction for loading.

The question therefore is how far to go:

1. Eagerly load the configuration files and run the parsing and merging just-in-time
   - The build process is tweaked to add a pause point. Files are loaded into memory via a thread, but loaded on first access.
   - EagerIO Tags start loading their IO near when they may be accessed.
2. Load as much IO as possible in the background.
   - The build process is shoved wholly into a thread.
   - EagerIO Tags start loading their IO as soon as possible.
   - Will have a performance impact due to GIL.
   - Lazy is left to the tags.

The point of Laziness was for pruning, having many libraries share one configuration and then pulling out only what each they needed, if a configuration wasn't needed by an application, it would not be loaded, and so on. Basically, laziness minimizes unintended side effects for teams using libraries without understanding the details.

The direction of EagerIO I've chosen seems to be one where intent matters.

Option 2 is the simplest to implement and is closest to the idea of doing all the loading during the import phase, so the cost at execution is minimal (though that is a cloud-centric cost optimization).

Option 1 has very behind-the-scenes magic.

With EagerIO being more an exploration at the point in time, Option 2 is more worth the time than Option 1.

---

Another question in implementation is optionality:

- Opt-In: Libraries and Apps choose to use EagerIO per Configuration and independently.
- Force-In: Apps and end-users choose to use EagerIO for all Configurations.

Fundamentally, "Opt-In" is the lowest risk:

- A User can only break themselves with EagerIO.
- Testing configuration option is bound to the library or application, so the testing combinations and modes isn't required for libraries.
- Intent matters.

:::

## Summary

EagerIO is an optional feature set that undoes some of the laziness of the library's default behavior, so that Fetch calls are non-blocking (or, at least, minimally blocking).

- [**EagerIO Tags**](#using-eagerio-tags) run IO in a background thread.
  - Available EagerIO Tags are found in the [EagerIO Tag Table](yaml.md#eagerio-tag-table).
  - The thread is launched at Load Time.
    - Because of this, EagerIO Tags can at most support the _Reduced Interpolation Syntax_ for IO operations.
  - Logic is still run at Fetch.
  - The performance cost of the thread due to the GIL is minimal.
  - Currently, EagerIO Tags run their IO regardless of pruning.
- [**EagerIO Loading**](#using-eagerio-loading) loads and build the configuration in a background thread.
  - Call {py:meth}`.LazyLoadConfiguration.eager_load` to use EagerIO Loading.
  - The thread is launched when {py:meth}`~.LazyLoadConfiguration.eager_load` is called.
  - Load, Merge, and Build all occur in the thread.
    - EagerIO Tags spawn at their thread from this thread.
  - The performance cost of the thread due to the GIL is maximal.
    - Python will interlace configuration loading with the main thread until loading is complete.
- You can use EagerIO Tags and EagerIO Loading independently or together.

:::{note}

EagerIO is not required with {py:mod}`asyncio`, but is an option to avoid IO blocking within the Event Loop.

:::

---

## Using EagerIO Tags

There is no outward difference between using a Lazy Tag vs. EagerIO Tag.

The following examples return the same data with the same interface:

````{list-table}
:header-rows: 1
:width: 75%
:widths: 1 1
:align: center

* - Lazy Tag
  - EagerIO Tag
* - ```yaml
    data: !ParseFile data.yaml
    ```
  - ```yaml
    data: !EagerParseFile data.yaml
    ```
````

- [`!EagerParseFile`](yaml.md#parsefile--optionalparsefile):
  - **Load Time:** In the background, `data.yaml` begins loading into memory, as soon as the configuration is loaded.
  - **First Fetch:** `data.yaml` is parsed when the `data` setting is fetched.
- [`!ParseFile`](yaml.md#parsefile--optionalparsefile):
  - **Load Time:** Nothing special happens.
  - **First Fetch:** `data.yaml` is loaded into memory and then parsed when the `data` setting is fetched.

## Using EagerIO Loading

There is no interface difference between using {py:meth}`.LazyLoadConfiguration.as_typed` and {py:meth}`.LazyLoadConfiguration.eager_load`.

:::{note}
If you want EagerIO Loading without type annotations, just past {py:class}`.Configuration` to {py:meth}`~.LazyLoadConfiguration.eager_load`.
:::

The following examples are used identically:

````{list-table}
:header-rows: 1
:width: 75%
:widths: 1 1
:align: center

* - Lazy Loading
  - EagerIO Loading
* - ```python
    class Settings(Configuration):
      ...

    CONFIG = LazyLoadConfiguration(
      ...
    ).as_typed(Settings)
    ```
  - ```python
    class Settings(Configuration):
      ...

    CONFIG = LazyLoadConfiguration(
      ...
    ).eager_load(Settings)
    ```
````

- {py:meth}`~.LazyLoadConfiguration.eager_load` will immediately start loading and building the configuration in the background.
  - This background load will take away some immediate performance, due to the GIL, but once complete there is no performance impact.
- {py:meth}`~.LazyLoadConfiguration.as_typed` will wait until an attribute is first fetched, before loading and building the configuration.

---

## Creating Custom EagerIO Tags

Creating an EagerIO Tag follows the [standard custom tag creation](plugins.md#writing-your-own-tag), but replaces the Laziness Decorator and doesn't support Interpolate Decorator.

### Example

```python
import typing

from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Root,
    Tag,
    string_tag,
)
from granular_configuration_language.yaml.decorators.eager_io import (
    EagerIOBinaryFile,
    EagerIOTextFile,
    as_eager_io,
    as_eager_io_with_root_and_load_options,
    eager_io_binary_loader_interpolates,
    eager_io_text_loader_interpolates,
)
from granular_configuration_language.yaml.file_ops.binary import read_binary_data
from granular_configuration_language.yaml.file_ops.yaml import load_from_file


@string_tag(Tag("!EagerParseFile"))             # Tag Type Decorator
@as_eager_io_with_root_and_load_options(        # EagerIO Decorator
  eager_io_text_loader_interpolates
)
# @with_tag                                     # (Optional) With Attribute Decorator
def tag(                                        # Function Signature
  value: EagerIOTextFile,
  root: Root,
  options: LoadOptions
) -> typing.Any:
    return load_from_file(value, options, root) # Tag Logic


@string_tag(Tag("!EagerLoadBinary"))              # Tag Type Decorator
@as_eager_io(eager_io_binary_loader_interpolates) # EagerIO Decorator
# @with_tag                                       # (Optional) With Attribute Decorator
def eager(file: EagerIOBinaryFile) -> bytes:     # Function Signature
    return read_binary_data(file)                 # Tag Logic
```

<br>

See standard custom tag document for the following:

- [](plugins.md#function-signature)
- [](plugins.md#tag-type-decorator)
- [](plugins.md#with-attribute-decorator)

### EagerIO Decorator

:::{caution}

Cannot be used with [](plugins.md#laziness-decorator) or [Interpolate Decorator](plugins.md#interpolate-decorator).

:::

- Defines the tag to be an EagerIO tag and defines the required positional parameters.
- The EagerIO Decorator is always a decorator factory.
  - EagerIO Decorator takes in an EagerIO Preprocessor that will be run eagerly.
  - _Positional Parameters_ - `(value: ..., tag: Tag, options: LoadOptions)`
    - `value` of the EagerIO Preprocessor's type is determined by [Tag Type Decorator](plugins.md#tag-type-decorator).
- The `value` of the Function Signature's type is determined by the output of EagerIO Preprocessor.
- Provided EagerIO Preprocessors:
  - Loading a text file eagerly:
    - {py:func}`.eager_io_text_loader`
      - Supports: {py:class}`.string_tag`
      - Outputs: {py:class}`.EagerIOTextFile`
    - {py:func}`.eager_io_text_loader_interpolates`
      - Supports: {py:class}`.string_tag`
      - Outputs: {py:class}`.EagerIOTextFile`
      - Applies _Reduced Interpolation Syntax_ to {py:class}`str` parameter.
  - Loading a binary file eagerly:
    - {py:func}`.eager_io_binary_loader`
      - Supports: {py:class}`.string_tag`
      - Outputs: {py:class}`.EagerIOBinaryFile`
    - {py:func}`.eager_io_binary_loader_interpolates`
      - Supports: {py:class}`.string_tag`
      - Outputs: {py:class}`.EagerIOBinaryFile`
      - Applies _Reduced Interpolation Syntax_ to {py:class}`str` parameter.
- Provided EagerIO Decorators:
  - {py:func}`.as_eager_io`
    - _Positional Parameters_ - `(value: ... )`
  - {py:func}`.as_eager_io_with_root_and_load_options`
    - _Positional Parameters_ - `value: ..., root: Root, options: LoadOptions`

---

## Implementation Notes

- All threads are managed using a {py:class}`~concurrent.futures.Future` from {py:class}`concurrent.futures.ThreadPoolExecutor` pools.
  - There is no optimization to have a shared pool per {py:class}`.LazyLoadConfiguration` at this time.
    - If EagerIO finds use, shared pools can be requested.
  - Pools have a `max_worker` count of 1, because each pool does one thing.
