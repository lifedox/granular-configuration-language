import os
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from granular_configuration._json import dumps
from granular_configuration.yaml import loads


def test_date() -> None:
    output = loads("!Date 2012-10-31")

    assert output == date(2012, 10, 31)
    assert dumps(output) == '"2012-10-31"'


def test_date_compressed() -> None:
    output = loads("!Date 20121031")

    assert output == date(2012, 10, 31)
    assert dumps(output) == '"2012-10-31"'


def test_date_from_env() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "20121031"}):
        output = loads("!Date ${unreal_env_variable}")

        assert output == date(2012, 10, 31)


def test_datetime_tz_less() -> None:
    output = loads("!DateTime 2012-10-31T13:12:09")

    assert output == datetime(2012, 10, 31, 13, 12, 9)
    assert dumps(output) == '"2012-10-31T13:12:09"'


def test_datetime_tz_less_compressed() -> None:
    output = loads("!DateTime 20121031T131209")

    assert output == datetime(2012, 10, 31, 13, 12, 9)
    assert dumps(output) == '"2012-10-31T13:12:09"'


def test_datetime_utc() -> None:
    output = loads("!DateTime 2012-10-31T13:12:09Z")

    assert output == datetime(2012, 10, 31, 13, 12, 9, tzinfo=timezone.utc)
    assert dumps(output) == '"2012-10-31T13:12:09+00:00"'


def test_datetime_utc_compressed() -> None:
    output = loads("!DateTime 20121031T131209Z")

    assert output == datetime(2012, 10, 31, 13, 12, 9, tzinfo=timezone.utc)
    assert dumps(output) == '"2012-10-31T13:12:09+00:00"'


def test_datetime_cst() -> None:
    output = loads("!DateTime 2012-10-31T13:12:09-06:00")

    assert output == datetime(2012, 10, 31, 13, 12, 9, tzinfo=timezone(timedelta(hours=-6)))
    assert dumps(output) == '"2012-10-31T13:12:09-06:00"'


def test_datetime_cst_compressed() -> None:
    output = loads("!DateTime 20121031T131209-0600")

    assert output == datetime(2012, 10, 31, 13, 12, 9, tzinfo=timezone(timedelta(hours=-6)))
    assert dumps(output) == '"2012-10-31T13:12:09-06:00"'


def test_datetime_from_env() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "20121031T131209-0600"}):
        output = loads("!DateTime ${unreal_env_variable}")

    assert output == datetime(2012, 10, 31, 13, 12, 9, tzinfo=timezone(timedelta(hours=-6)))
