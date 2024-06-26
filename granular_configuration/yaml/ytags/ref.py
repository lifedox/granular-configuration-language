import operator as op
import re
import typing as typ

import jsonpath

from granular_configuration.exceptions import (
    JSONPathMustPointToASingleValue,
    JSONPathMustStartFromRoot,
    JSONPathOnlyWorksOnMappings,
    JSONPathQueryMatchFailed,
)
from granular_configuration.yaml.classes import LazyEval, Root
from granular_configuration.yaml.decorators import Tag, as_lazy_with_root, string_tag
from granular_configuration.yaml.ytags.merge import merge_tag

SUB_PATTERN: typ.Pattern[str] = re.compile(r"(\$\{(?P<contents>.*?)\})")


def _resolve_pointer(query: str, root: typ.Mapping) -> typ.Any:
    try:
        not_found = object()

        result = jsonpath.JSONPointer(query).resolve(root, default=not_found)

        if result is not_found:
            raise JSONPathQueryMatchFailed(f"JSON Pointer `{query}` did not find a match.")
        else:
            return result

    except RecursionError:
        raise RecursionError(
            (
                f"JSON Pointer `{query}` caused a recursion error. Please check your configuration for a self-referencing loop."
            )
        ) from None


def _resolve_path(query: str, root: typ.Mapping) -> typ.Any:
    try:
        result = list(map(op.attrgetter("value"), jsonpath.finditer(query, root)))

        if len(result) == 1:
            return result[0]
        elif len(result) == 0:
            raise JSONPathQueryMatchFailed(f"JSON Path `{query}` did not find a match.")
        else:
            return repr(result)
            raise JSONPathMustPointToASingleValue(f"JSON Path `{query}` did not find a match.")  # pragma: no cover

    except RecursionError:  # pragma: no cover
        # Coverage is missing this, but it could be the RecursionError and the upstream catch-and-replace
        # Replacing RecursionError with Exception shows that test is running
        raise RecursionError(
            (
                f"JSON Path `{query}` caused a recursion error. Please check your configuration for a self-referencing loop."
            )
        ) from None


def resolve_json_ref(query: str, root: Root) -> typ.Any:
    if isinstance(root, LazyEval) and root.tag == merge_tag:
        raise RecursionError(
            f"JSON Query `{query}` attempted recursion. Please check your configuration for a self-referencing loop."
        )
    elif not isinstance(root, typ.Mapping):
        raise JSONPathOnlyWorksOnMappings(f"JSONPath `{query}` was tried on `{repr(root)}`")
    elif query.startswith("$"):
        return _resolve_path(query, root)
    elif query.startswith("/"):
        return _resolve_pointer(query, root)
    else:
        raise JSONPathMustStartFromRoot(
            f"JSON query `{query}` must start with '$' for JSON Path or '/' for JSON Pointer"
        )


@string_tag(Tag("!Ref"))
@as_lazy_with_root
def handler(value: str, root: Root) -> str:
    return resolve_json_ref(value, root)
