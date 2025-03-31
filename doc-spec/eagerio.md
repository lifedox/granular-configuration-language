# EagerIO vs Laziness (`asyncio`)

:::{admonition} Philosophical Thought Process
:class: note
:collapsible: closed

{py:mod}`asyncio` is an important tool for concurrency.

While this library's interface is highly compatible with async code, since most of it is straightforward getting objects out of mappings. There are some places where the blocking code does exist.

Namely:

- The initial load of configuration.
- Any Tags that use IO.
- Any Tags that are CPU-intensive

I believe it is allowable to ignore the CPU-bound case. No Tag is inherently complex (users are in control) and the GIL exists. That leaves two categories for IO-bound cases.

---

Starting with IO-bound Tags, the biggest thing to bear in mind is that tags are optional, most tags act on in memory data (environment variables and configuration data), and all tags run-once and are cached immediately afterward.

The first thought was to make {py:class}`~collections.abc.Awaitable` proxy for {py:meth}`~object.__getattr__` calls. It would maximum the opportunities for coroutines to run and enables the few IO-bound Tags to run waiting. But most all the time, the wrapper would exist to immediately return a primitive. The `await` would just be chained overhead. Typing would be annoying or back to just using {py:data}`~typing.Any`. Realistically, the most optimal version would be an async {py:func}`~operator.attrgetter`-like method (Reminder: {py:func}`~operator.attrgetter` requires type checker to implement special behavior).

So, instead of using {py:mod}`asyncio` that leaves meeting {py:mod}`asyncio` in the middle. Since we cannot `await`, and we want coroutines to avoid waiting for IO, what if we ran that IO-bound (like async would) ahead of time, so when a coroutine requests data, the IO is probably already loaded. This put the "eager" in **Eager**IO.

The only challenge is when to run the IO of the EagerIO Tags. It needs to be compatible with synchronous and asynchronous code, able to handle users not doing a step, and libraries. In the end, the simplest, most maintainable option was to start the IO at load time, so there was no behavioral or interface change. User opts into EagerIO by using an EagerIO Tag.

---

That leaves the question of the initial load. With not using `await` for Tags, the same solution of pushing IO into threads is the direction for loading.

The question therefore is how far to go:

1. Eagerly load the configuration files and run the parsing and merging just-in-time
2. Load as much IO as possible in the background.

With Option 1, the build process is tweaked to add a pause point. The

Another question in implementation is optionality:

- Opt-In: Libraries and Apps choose to use EagerIO per Configuration.
- Force-In: Apps and end-users choose to use EagerIO for all Configurations.

:::
