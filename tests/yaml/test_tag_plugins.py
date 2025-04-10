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
    *options: str,
) -> str:
    available = AvailablePlugins if script == "available_plugins" else AvailableTags

    # For coverage:
    if "--long" in options:
        caller = op.methodcaller(type, shorten=False)
    else:
        caller = op.methodcaller(type)

    caller(available(handlers.get_subset(*tags)))

    config_env = dict(G_CONFIG_DISABLE_TAGS=",".join(map(op.attrgetter("tag"), handlers.get_difference(*tags))))

    return subprocess.check_output(
        [sys.executable, "-m", "granular_configuration_language." + script, type, *options], env=config_env
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


TAGS_TO_TEST_WITH = ("!Del", "!Func", "!UUID", "!Merge", "!Sub", "!EagerParseFile")


def test_available_tags_csv() -> None:
    output = call("available_tags", "csv", TAGS_TO_TEST_WITH)

    print(output)

    assert (
        output
        == """\
category,tag,type,interpolates,lazy,returns,eio_inner_type
Formatter,!Sub,str,full,,str,
Manipulator,!Del,str,,NOT_LAZY,str,
Manipulator,!Merge,list[Any],,,Configuration,
Parser,!EagerParseFile,str,reduced,EAGER_IO,Any,EagerIOTextFile
Typer,!Func,str,reduced,,Callable,
Typer,!UUID,str,reduced,,UUID,
"""
    )


def test_available_tags_json() -> None:
    output = call("available_tags", "json", TAGS_TO_TEST_WITH)

    print(output)

    assert (
        output
        == """\
{
  "Formatter": {
    "!Sub": {
      "eio_inner_type": null,
      "interpolates": "full",
      "lazy": null,
      "returns": "str",
      "type": "str"
    }
  },
  "Manipulator": {
    "!Del": {
      "eio_inner_type": null,
      "interpolates": null,
      "lazy": "NOT_LAZY",
      "returns": "str",
      "type": "str"
    },
    "!Merge": {
      "eio_inner_type": null,
      "interpolates": null,
      "lazy": null,
      "returns": "Configuration",
      "type": "list[Any]"
    }
  },
  "Parser": {
    "!EagerParseFile": {
      "eio_inner_type": "EagerIOTextFile",
      "interpolates": "reduced",
      "lazy": "EAGER_IO",
      "returns": "Any",
      "type": "str"
    }
  },
  "Typer": {
    "!Func": {
      "eio_inner_type": null,
      "interpolates": "reduced",
      "lazy": null,
      "returns": "Callable",
      "type": "str"
    },
    "!UUID": {
      "eio_inner_type": null,
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
    output = call("available_tags", "table", TAGS_TO_TEST_WITH)

    print(output)

    assert can_table, "test with tabulate installed"
    assert (
        output
        == """\
category     tag              type       interpolates    lazy      returns        eio_inner_type
-----------  ---------------  ---------  --------------  --------  -------------  ----------------
Formatter    !Sub             str        full                      str
Manipulator  !Del             str                        NOT_LAZY  str
Manipulator  !Merge           list[Any]                            Configuration
Parser       !EagerParseFile  str        reduced         EAGER_IO  Any            EagerIOTextFile
Typer        !Func            str        reduced                   Callable
Typer        !UUID            str        reduced                   UUID
"""
    )


def test_table_missing() -> None:
    tags = handlers.get_subset(*TAGS_TO_TEST_WITH)
    output = AvailableTags(tags).table(_force_missing=True)

    print(output)

    assert (
        output
        == """\
The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies"""
    )


def test_available_plugins_csv() -> None:
    output = call("available_plugins", "csv", TAGS_TO_TEST_WITH)

    print(output)

    assert (
        output
        == """\
plugin,category,tag,handler,needs_root_condition,eager_io
<gcl-built-in>,Formatter,!Sub,granular_configuration_language.yaml._tags._sub.tag,interpolation_needs_ref_condition,
<gcl-built-in>,Manipulator,!Del,granular_configuration_language.yaml._tags._del.tag,,
<gcl-built-in>,Manipulator,!Merge,granular_configuration_language.yaml._tags._merge.tag,,
<gcl-built-in>,Parser,!EagerParseFile,granular_configuration_language.yaml._tags._eager_parse_file.tag,,eager_io_text_loader_interpolates
<gcl-built-in>,Typer,!UUID,granular_configuration_language.yaml._tags._uuid.tag,,
official_extra,Typer,!Func,granular_configuration_language.yaml._tags.func_and_class.func_,,
"""
    )


def test_available_plugins_json() -> None:
    output = call("available_plugins", "json", TAGS_TO_TEST_WITH)

    print(output)

    assert (
        output
        == """\
{
  "<gcl-built-in>": {
    "Formatter": {
      "!Sub": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags._sub.tag",
        "needs_root_condition": "interpolation_needs_ref_condition"
      }
    },
    "Manipulator": {
      "!Del": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags._del.tag",
        "needs_root_condition": null
      },
      "!Merge": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags._merge.tag",
        "needs_root_condition": null
      }
    },
    "Parser": {
      "!EagerParseFile": {
        "eager_io": "eager_io_text_loader_interpolates",
        "handler": "granular_configuration_language.yaml._tags._eager_parse_file.tag",
        "needs_root_condition": null
      }
    },
    "Typer": {
      "!UUID": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags._uuid.tag",
        "needs_root_condition": null
      }
    }
  },
  "official_extra": {
    "Typer": {
      "!Func": {
        "eager_io": null,
        "handler": "granular_configuration_language.yaml._tags.func_and_class.func_",
        "needs_root_condition": null
      }
    }
  }
}
"""
    )


def test_available_plugins_table() -> None:
    output = call("available_plugins", "table", TAGS_TO_TEST_WITH)

    print(output)

    assert can_table, "test with tabulate installed"
    assert (
        output
        == """\
plugin          category     tag              handler                      needs_root_condition    eager_io
--------------  -----------  ---------------  ---------------------------  ----------------------  ----------
<gcl-built-in>  Formatter    !Sub             <gcl>._sub.tag               ntrpl_needs_ref
<gcl-built-in>  Manipulator  !Del             <gcl>._del.tag
<gcl-built-in>  Manipulator  !Merge           <gcl>._merge.tag
<gcl-built-in>  Parser       !EagerParseFile  <gcl>._eager_parse_file.tag                          text_ntrpl
<gcl-built-in>  Typer        !UUID            <gcl>._uuid.tag
official_extra  Typer        !Func            <gcl>.func_and_class.func_

Shortenings:
`<gcl>` = `granular_configuration_language.yaml._tags`
`ntrpl_needs_ref` = `interpolation_needs_ref_condition`
`text_ntrpl` = `eager_io_text_loader_interpolates`
"""
    )


def test_available_plugins_table_long() -> None:
    output = call("available_plugins", "table", TAGS_TO_TEST_WITH, "--long")

    print(output)

    assert can_table, "test with tabulate installed"
    assert (
        output
        == """\
plugin          category     tag              handler                                                           needs_root_condition               eager_io
--------------  -----------  ---------------  ----------------------------------------------------------------  ---------------------------------  ---------------------------------
<gcl-built-in>  Formatter    !Sub             granular_configuration_language.yaml._tags._sub.tag               interpolation_needs_ref_condition
<gcl-built-in>  Manipulator  !Del             granular_configuration_language.yaml._tags._del.tag
<gcl-built-in>  Manipulator  !Merge           granular_configuration_language.yaml._tags._merge.tag
<gcl-built-in>  Parser       !EagerParseFile  granular_configuration_language.yaml._tags._eager_parse_file.tag                                     eager_io_text_loader_interpolates
<gcl-built-in>  Typer        !UUID            granular_configuration_language.yaml._tags._uuid.tag
official_extra  Typer        !Func            granular_configuration_language.yaml._tags.func_and_class.func_
"""
    )


def test_available_tags_help() -> None:
    config_env = dict(G_CONFIG_DISABLE_TAGS=",".join(map(op.attrgetter("tag"), handlers)))
    output = subprocess.check_output(
        [sys.executable, "-m", "granular_configuration_language.available_tags", "--help"],
        env=config_env,
    ).decode()

    print(output)

    assert (
        output
        == """\
usage: python -m granular_configuration_language.available_tags
       [-h] [{csv,json,table}]

Shows available tags

positional arguments:
  {csv,json,table}  Mode, default={table}

options:
  -h, --help        show this help message and exit

The "table" option requires `tabulate` to be installed. You can use the
"printing" extra to install the needed dependencies
"""
    )


def test_available_plugins_help() -> None:
    config_env = dict(G_CONFIG_DISABLE_TAGS=",".join(map(op.attrgetter("tag"), handlers)))
    output = subprocess.check_output(
        [sys.executable, "-m", "granular_configuration_language.available_plugins", "--help"],
        env=config_env,
    ).decode()
    print(output)

    assert (
        output
        == """\
usage: python -m granular_configuration_language.available_plugins
       [-h] [--long] [{csv,json,table}]

Shows available plugins

positional arguments:
  {csv,json,table}  Mode, default={table}

options:
  -h, --help        show this help message and exit
  --long, -l        In "table" mode, use long names. "Shortenings" lookup will
                    not print.

The "table" option requires `tabulate` to be installed. You can use the
"printing" extra to install the needed dependencies
"""
    )


def test_available_tags_help_can_table_false() -> None:
    config_env = dict(
        G_CONFIG_DISABLE_TAGS=",".join(map(op.attrgetter("tag"), handlers)),
        G_CONFIG_FORCE_CAN_TABLE_FALSE="TRUE",
    )
    output = subprocess.check_output(
        [sys.executable, "-m", "granular_configuration_language.available_tags", "--help"],
        env=config_env,
    ).decode()

    print(output)

    assert (
        output
        == """\
usage: python -m granular_configuration_language.available_tags
       [-h] [{csv,json}]

Shows available tags

positional arguments:
  {csv,json}  Mode, default={csv}

options:
  -h, --help  show this help message and exit

The "table" option requires `tabulate` to be installed. You can use the
"printing" extra to install the needed dependencies
"""
    )


def test_available_plugins_help_can_table_false() -> None:
    config_env = dict(
        G_CONFIG_DISABLE_TAGS=",".join(map(op.attrgetter("tag"), handlers)),
        G_CONFIG_FORCE_CAN_TABLE_FALSE="TRUE",
    )
    output = subprocess.check_output(
        [sys.executable, "-m", "granular_configuration_language.available_plugins", "--help"],
        env=config_env,
    ).decode()
    print(output)

    assert (
        output
        == """\
usage: python -m granular_configuration_language.available_plugins
       [-h] [{csv,json}]

Shows available plugins

positional arguments:
  {csv,json}  Mode, default={csv}

options:
  -h, --help  show this help message and exit

The "table" option requires `tabulate` to be installed. You can use the
"printing" extra to install the needed dependencies
"""
    )


def test_all_attributes_have_tags() -> None:
    for attribute in tracker:
        assert attribute.tag
