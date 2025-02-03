import collections.abc as tabc
from operator import attrgetter

tracker_id = attrgetter("__module__", "__name__", "__qualname__")

with_ref: set[tuple[str, str, str]] = set()
without_ref: set[tuple[str, str, str]] = set()
not_lazy: set[tuple[str, str, str]] = set()


def track_as_with_ref(func: tabc.Callable) -> None:
    with_ref.add(tracker_id(func))


def is_with_ref(func: tabc.Callable) -> bool:
    return tracker_id(func) in with_ref


def track_as_without_ref(func: tabc.Callable) -> None:
    without_ref.add(tracker_id(func))


def is_without_ref(func: tabc.Callable) -> bool:
    return tracker_id(func) in without_ref


def track_as_not_lazy(func: tabc.Callable) -> None:
    not_lazy.add(tracker_id(func))


def is_not_lazy(func: tabc.Callable) -> bool:
    return tracker_id(func) in not_lazy
