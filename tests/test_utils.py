# -*- coding: utf-8 -*-
"""时间参数解析。"""

from __future__ import annotations

from datetime import datetime

import pytest

from yingdao_rpa.utils import parse_timestamp


def test_int_passthrough():
    assert parse_timestamp(1710000000) == 1710000000


def test_epoch_string():
    assert parse_timestamp("1710000000") == 1710000000


def test_empty_values():
    assert parse_timestamp(None) is None
    assert parse_timestamp("  ") is None


def test_date_is_interpreted_in_local_timezone():
    expected = int(datetime(2026, 1, 1).astimezone().timestamp())

    assert parse_timestamp("2026-01-01") == expected


def test_datetime_with_seconds():
    expected = int(datetime(2026, 1, 1, 12, 30, 0).astimezone().timestamp())

    assert parse_timestamp("2026-01-01 12:30:00") == expected


def test_iso_with_timezone():
    assert parse_timestamp("2026-01-01T00:00:00+08:00") == 1767196800


def test_millisecond_timestamp_is_rejected():
    with pytest.raises(ValueError, match="毫秒"):
        parse_timestamp("1767225600000")


def test_invalid_value_reports_field():
    with pytest.raises(ValueError, match="过期时间"):
        parse_timestamp("2026/01/01", field="过期时间")
