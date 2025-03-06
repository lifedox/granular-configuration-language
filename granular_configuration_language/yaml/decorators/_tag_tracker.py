from __future__ import annotations

import collections.abc as tabc
import os
from operator import attrgetter

TrackerId = tuple[str, str, str]
tracker_id = attrgetter("__module__", "__name__", "__qualname__")

with_ref: set[TrackerId] = set()
without_ref: set[TrackerId] = set()
not_lazy: set[TrackerId] = set()
needs_root_condition: dict[TrackerId, tabc.Callable] = dict()

ENABLED = os.environ.get("G_CONFIG_ENABLE_TAG_TRACKER") == "TRUE"


def track_as_with_ref(func: tabc.Callable) -> None:
    if ENABLED:  # pragma: no cover  # coverage shown by test output
        with_ref.add(tracker_id(func))


def is_with_ref(func: tabc.Callable) -> bool:
    return tracker_id(func) in with_ref


def track_as_without_ref(func: tabc.Callable) -> None:
    if ENABLED:  # pragma: no cover  # coverage shown by test output
        without_ref.add(tracker_id(func))


def is_without_ref(func: tabc.Callable) -> bool:
    return tracker_id(func) in without_ref


def track_as_not_lazy(func: tabc.Callable) -> None:
    if ENABLED:  # pragma: no cover  # coverage shown by test output
        not_lazy.add(tracker_id(func))


def is_not_lazy(func: tabc.Callable) -> bool:
    return tracker_id(func) in not_lazy


def track_needs_root_condition(func: tabc.Callable, condition: tabc.Callable) -> None:
    if ENABLED:  # pragma: no cover  # coverage shown by test output
        needs_root_condition[tracker_id(func)] = condition


def get_needs_root_condition(func: tabc.Callable) -> tabc.Callable | None:
    return needs_root_condition.get(tracker_id(func))
