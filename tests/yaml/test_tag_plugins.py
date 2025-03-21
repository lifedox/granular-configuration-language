from __future__ import annotations

import operator as op
import os
import subprocess
import sys
import typing as typ
from unittest.mock import patch

import pytest

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml._tags import handlers
from granular_configuration_language.yaml.decorators._tag_loader import load_tags
from granular_configuration_language.yaml.decorators._tag_set import TagSet
from granular_configuration_language.yaml.decorators._tag_tracker import tracker
from granular_configuration_language.yaml.decorators._viewer import AvailablePlugins, AvailableTags, can_table


def call(
    script: typ.Literal["available_tags"] | typ.Literal["available_plugins"],
    type: typ.Literal["csv"] | typ.Literal["json"] | typ.Literal["table"],
    tags: tuple[str, ...],
    /,
) -> str:
    available = AvailablePlugins if script == "available_plugins" else AvailableTags

    # For coverage:
    op.methodcaller(type)(available(handlers.get_subset(*tags)))

    config_env = dict(G_CONFIG_DISABLE_TAGS=",".join(map(op.attrgetter("tag"), handlers.get_difference(*tags))))

    return subprocess.check_output(
        [sys.executable, "-m", "granular_configuration_language." + script, type], env=config_env
    ).decode()


def test_singletonness() -> None:
    assert tuple(load_tags()) == tuple(load_tags())


def test_disabling_official_extra_tags_removes_Func_and_Class() -> None:
    assert load_tags().has_tags("!Func", "!Class")
    assert load_tags(disable_plugins={"official_extra"}).does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": ""}):
        assert load_tags().has_tags("!Func", "!Class")
    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": ","}):
        assert load_tags().has_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": "official_extra"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": "official_extra,"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": ",official_extra,"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": "official_extra "}):
        assert load_tags().does_not_have_tags("!Func", "!Class")


def test_disabling_tags_removes_those_tags() -> None:
    assert load_tags().has_tags("!Func", "!Class")
    assert load_tags(disable_tags={"!Func", "!Class"}).does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": ""}):
        assert load_tags().has_tags("!Func", "!Class")
    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": ","}):
        assert load_tags().has_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": "!Func,!Class"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": "!Func,"}):
        assert load_tags().does_not_have_tags("!Func")
        assert load_tags().has_tags("!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": ",!Func,!Class,"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": "!Func, !Class "}):
        assert load_tags().does_not_have_tags("!Func", "!Class")


def test_trying_to_override_a_tag_errors() -> None:
    tag = next(iter(handlers))
    with pytest.raises(ErrorWhileLoadingTags):
        TagSet((tag, tag))


def test_available_tags_csv() -> None:
    output = call("available_tags", "csv", ("!Del", "!UUID", "!Merge", "!Sub"))

    print(output)

    assert (
        output
        == """\
category,tag,type,interpolates,lazy,returns
Formatter,!Sub,str,full,,str
Manipulator,!Del,str,,NOT_LAZY,str
Manipulator,!Merge,list[Any],,,Configuration
Typer,!UUID,str,reduced,,UUID
"""
    )


def test_available_tags_json() -> None:
    output = call("available_tags", "json", ("!Del", "!UUID", "!Merge", "!Sub"))

    print(output)

    assert (
        output
        == """\
{
  "Formatter": {
    "!Sub": {
      "interpolates": "full",
      "lazy": null,
      "returns": "str",
      "type": "str"
    }
  },
  "Manipulator": {
    "!Del": {
      "interpolates": null,
      "lazy": "NOT_LAZY",
      "returns": "str",
      "type": "str"
    },
    "!Merge": {
      "interpolates": null,
      "lazy": null,
      "returns": "Configuration",
      "type": "list[Any]"
    }
  },
  "Typer": {
    "!UUID": {
      "interpolates": "reduced",
      "lazy": null,
      "returns": "UUID",
      "type": "str"
    }
  }
}
"""
    )


def test_available_tags_table() -> None:
    output = call("available_tags", "table", ("!Del", "!UUID", "!Merge", "!Sub"))

    print(output)

    assert can_table, "test with tabulate installed"
    assert (
        output
        == """\
category     tag     type       interpolates    lazy      returns
-----------  ------  ---------  --------------  --------  -------------
Formatter    !Sub    str        full                      str
Manipulator  !Del    str                        NOT_LAZY  str
Manipulator  !Merge  list[Any]                            Configuration
Typer        !UUID   str        reduced                   UUID
"""
    )


def test_table_missing() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")
    output = AvailableTags(tags).table(_force_missing=True)

    print(output)

    assert (
        output
        == """\
The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies"""
    )


def test_available_plugins_csv() -> None:
    output = call("available_plugins", "csv", ("!Func", "!UUID", "!Merge", "!Sub", "!EagerParseFile"))

    print(output)

    assert (
        output
        == """\
plugin,category,tag,handler,needs_root_condition,eager_io
<gcl-built-in>,Formatter,!Sub,granular_configuration_language.yaml._tags._sub.handler,interpolation_needs_ref_condition,
<gcl-built-in>,Manipulator,!Merge,granular_configuration_language.yaml._tags._merge.handler,,
<gcl-built-in>,Parser,!EagerParseFile,granular_configuration_language.yaml._tags._eager_parse_file.handler,,eager_io_text_loader
<gcl-built-in>,Typer,!UUID,granular_configuration_language.yaml._tags._uuid.handler,,
official_extra,Typer,!Func,granular_configuration_language.yaml._tags.func_and_class.func_handler,,
"""
    )


def test_available_plugins_json() -> None:
    output = call("available_plugins", "json", ("!Func", "!UUID", "!Merge", "!Sub", "!EagerParseFile"))

    print(output)

    assert (
        output
        == """\
{
  "<gcl-built-in>": {
    "Formatter": {
      "!Sub": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags._sub.handler",
        "needs_root_condition": "interpolation_needs_ref_condition"
      }
    },
    "Manipulator": {
      "!Merge": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags._merge.handler",
        "needs_root_condition": null
      }
    },
    "Parser": {
      "!EagerParseFile": {
        "eager_io": "eager_io_text_loader",
        "handler": "granular_configuration_language.yaml._tags._eager_parse_file.handler",
        "needs_root_condition": null
      }
    },
    "Typer": {
      "!UUID": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags._uuid.handler",
        "needs_root_condition": null
      }
    }
  },
  "official_extra": {
    "Typer": {
      "!Func": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags.func_and_class.func_handler",
        "needs_root_condition": null
      }
    }
  }
}
"""
    )


def test_available_plugins_table() -> None:
    output = call("available_plugins", "table", ("!Func", "!UUID", "!Merge", "!Sub", "!EagerParseFile"))

    print(output)

    assert can_table, "test with tabulate installed"
    assert (
        output
        == """\
plugin          category     tag              handler                                                                 needs_root_condition               eager_io
--------------  -----------  ---------------  ----------------------------------------------------------------------  ---------------------------------  --------------------
<gcl-built-in>  Formatter    !Sub             granular_configuration_language.yaml._tags._sub.handler                 interpolation_needs_ref_condition
<gcl-built-in>  Manipulator  !Merge           granular_configuration_language.yaml._tags._merge.handler
<gcl-built-in>  Parser       !EagerParseFile  granular_configuration_language.yaml._tags._eager_parse_file.handler                                       eager_io_text_loader
<gcl-built-in>  Typer        !UUID            granular_configuration_language.yaml._tags._uuid.handler
official_extra  Typer        !Func            granular_configuration_language.yaml._tags.func_and_class.func_handler
"""
    )


def test_all_attributes_have_tags() -> None:
    for attribute in tracker:
        assert attribute.tag
