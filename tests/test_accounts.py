# -*- coding: utf-8 -*-
"""企业版账号后缀：规范化与补全。"""

from __future__ import annotations

import pytest

from yingdao_rpa.accounts import normalize_suffix, resolve_account_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ""),
        (None, ""),
        ("csqy1", "@csqy1"),
        ("@csqy1", "@csqy1"),
        ("  @csqy1  ", "@csqy1"),
    ],
)
def test_normalize_suffix(raw, expected):
    assert normalize_suffix(raw) == expected


@pytest.mark.parametrize("raw", ["@", "a@b", "@a@b"])
def test_normalize_suffix_rejects_invalid(raw):
    with pytest.raises(ValueError):
        normalize_suffix(raw)


def test_full_name_is_kept_as_is():
    assert resolve_account_name("ceshi1@other", "@csqy1") == "ceshi1@other"


def test_name_without_suffix_gets_config_suffix():
    assert resolve_account_name("ceshi1", "@csqy1") == "ceshi1@csqy1"


def test_suffix_is_normalized_before_appending():
    assert resolve_account_name("ceshi1", "csqy1") == "ceshi1@csqy1"


def test_missing_suffix_is_rejected():
    with pytest.raises(ValueError, match="缺少企业账号后缀"):
        resolve_account_name("ceshi1", "")


@pytest.mark.parametrize("name", ["ceshi1@", "@csqy1", " "])
def test_incomplete_names_are_rejected(name):
    with pytest.raises(ValueError):
        resolve_account_name(name, "@csqy1")
