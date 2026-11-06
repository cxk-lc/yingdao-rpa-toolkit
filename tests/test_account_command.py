# -*- coding: utf-8 -*-
"""account list：查询构造、分页聚合与干跑预览。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yingdao_rpa.client import ApiMeta
from yingdao_rpa.commands.account import (
    build_query,
    match_accounts,
    query_accounts,
    run_list,
)
from yingdao_rpa.config import Config
from yingdao_rpa.errors import ParamError
from yingdao_rpa.runtime import Runtime
from yingdao_rpa.utils import parse_timestamp

ACCOUNT_A = {
    "userUuid": "u-1",
    "loginAccount": "zhangsan@corp",
    "name": "张三",
    "phone": "13312345678",
    "role": "e_user",
    "roleName": "员工",
    "accountType": "basic",
    "accountTypeName": "基础账号",
    "latestLoginTime": "2026-01-01 10:00:00",
    "expiredTime": "2027-01-01 23:59:59",
}
ACCOUNT_B = {**ACCOUNT_A, "userUuid": "u-2", "loginAccount": "lisi@corp", "name": "李四"}
ACCOUNT_C = {**ACCOUNT_A, "userUuid": "u-3", "loginAccount": "wangwu@corp", "name": "王五"}


class FakeClient:
    def __init__(self, payloads=None):
        self.payloads = list(payloads or [])
        self.calls: list[dict] = []
        self.last_meta = ApiMeta(base_url="https://example.test", api_code=200, api_success=True)

    def request(self, method, path, query=None, **kwargs):
        self.calls.append({"method": method, "path": path, "query": dict(query or {})})
        return self.payloads.pop(0) if len(self.payloads) > 1 else self.payloads[0]

    def preview(self, method, path, query=None, **kwargs):
        return {"method": method, "url": "https://example.test" + path, "query": query}


def make_runtime(client=None, dry_run: bool = False) -> Runtime:
    return Runtime(
        config=Config(
            base_url="https://example.test",
            access_key_id="ak",
            access_key_secret="sk",
        ),
        client=client or FakeClient([{"success": True, "code": 200, "data": []}]),
        dry_run=dry_run,
    )


def args(**overrides) -> SimpleNamespace:
    base = {
        "keyword": None,
        "phone": None,
        "account_type": None,
        "latest_login_begin": None,
        "latest_login_end": None,
        "expired_begin": None,
        "expired_end": None,
        "page": None,
        "size": None,
        "all": False,
        "max_pages": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def page(rows, page_no=1, pages=1, size=20, total=None):
    return {
        "success": True,
        "code": 200,
        "data": rows,
        "page": {
            "total": total if total is not None else len(rows),
            "size": size,
            "page": page_no,
            "pages": pages,
            "offset": (page_no - 1) * size,
            "order": "desc",
        },
    }


def test_query_defaults_to_first_page():
    assert build_query(args()) == {"page": 1, "size": 20}


def test_query_includes_filters():
    query = build_query(
        args(
            keyword=" 张三 ",
            phone="13312345678",
            account_type=["basic", "senior"],
            latest_login_begin="2026-01-01",
            latest_login_end="2026-02-01",
            page=2,
            size=50,
        )
    )

    assert query["accountKeyword"] == "张三"
    assert query["phone"] == "13312345678"
    assert query["accountTypes"] == ["basic", "senior"]
    assert query["latestLoginTimeBegin"] == parse_timestamp("2026-01-01")
    assert query["latestLoginTimeEnd"] == parse_timestamp("2026-02-01")
    assert (query["page"], query["size"]) == (2, 50)


def test_account_types_accept_comma_and_dedupe():
    query = build_query(args(account_type=["basic,senior", "basic"]))

    assert query["accountTypes"] == ["basic", "senior"]


@pytest.mark.parametrize("value", ["vip", "basic,vip"])
def test_unknown_account_type_is_rejected(value):
    with pytest.raises(ParamError, match="未知账号类型"):
        build_query(args(account_type=[value]))


@pytest.mark.parametrize(("field", "value"), [("size", 0), ("size", 101), ("page", 0)])
def test_page_and_size_are_validated(field, value):
    with pytest.raises(ParamError):
        build_query(args(**{field: value}))


def test_time_range_must_be_ordered():
    with pytest.raises(ParamError, match="不能晚于"):
        build_query(args(latest_login_begin="2026-02-01", latest_login_end="2026-01-01"))


def test_invalid_time_is_rejected():
    with pytest.raises(ParamError, match="格式无法识别"):
        build_query(args(expired_begin="not-a-date"))


def test_single_page_returns_items_and_page_info():
    client = FakeClient([page([ACCOUNT_A, ACCOUNT_B], page_no=1, pages=1)])

    result = run_list(args(), make_runtime(client))

    assert result["data"]["kind"] == "account_list"
    assert result["data"]["count"] == 2
    assert result["data"]["page"]["total"] == 2
    assert result["data"]["requested"] == {"all": False, "page": 1, "size": 20}
    assert client.calls[0]["query"] == {"page": 1, "size": 20}


def test_all_fetches_every_page():
    client = FakeClient(
        [
            page([ACCOUNT_A, ACCOUNT_B], page_no=1, pages=2, size=2, total=3),
            page([ACCOUNT_C], page_no=2, pages=2, size=2, total=3),
        ]
    )

    result = run_list(args(all=True, size=2), make_runtime(client))

    assert result["data"]["count"] == 3
    assert [call["query"]["page"] for call in client.calls] == [1, 2]
    assert result["data"]["requested"]["fetchedPages"] == 2
    assert result["warnings"] == []


def test_max_pages_stops_with_warning():
    client = FakeClient([page([ACCOUNT_A, ACCOUNT_B], page_no=1, pages=5, size=2, total=10)])

    result = run_list(args(all=True, size=2, max_pages=1), make_runtime(client))

    assert result["data"]["count"] == 2
    assert len(client.calls) == 1
    assert result["warnings"] and "max-pages" in result["warnings"][0]


def test_all_stops_on_short_page_without_page_info():
    payload = {"success": True, "code": 200, "data": [ACCOUNT_A]}
    client = FakeClient([payload])

    result = run_list(args(all=True, size=20), make_runtime(client))

    assert result["data"]["count"] == 1
    assert len(client.calls) == 1


def test_dry_run_shows_query_without_request():
    client = FakeClient([])

    result = run_list(
        args(keyword="张", account_type=["basic"], page=2, size=50),
        make_runtime(client, dry_run=True),
    )

    assert client.calls == []
    request = result["data"]["request"]
    assert request["method"] == "GET"
    assert request["query"]["accountKeyword"] == "张"
    assert request["query"]["accountTypes"] == ["basic"]
    assert request["query"]["page"] == 2


class PagedClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls: list[dict] = []

    def request(self, method, path, query=None, **kwargs):
        self.calls.append({"method": method, "path": path, "query": dict(query or {})})
        return self.payloads.pop(0)


def test_query_accounts_collects_pages():
    client = PagedClient(
        [
            page([ACCOUNT_A], page_no=1, pages=2, size=1, total=2),
            page([ACCOUNT_B], page_no=2, pages=2, size=1, total=2),
        ]
    )

    accounts = query_accounts(client, "ceshi", page_size=1, max_pages=3)

    assert len(accounts) == 2
    assert [call["query"]["page"] for call in client.calls] == [1, 2]


def test_match_accounts_prefers_login_local_part():
    accounts = [
        {"loginAccount": "other@x", "name": "ceshi1"},
        {"loginAccount": "ceshi1@y", "name": "张三"},
    ]

    matched = match_accounts(accounts, "ceshi1")

    assert [item["loginAccount"] for item in matched] == ["ceshi1@y"]


def test_match_accounts_falls_back_to_name():
    accounts = [{"loginAccount": "robot-01@x", "name": "ceshi1"}]

    matched = match_accounts(accounts, "ceshi1")

    assert [item["loginAccount"] for item in matched] == ["robot-01@x"]
