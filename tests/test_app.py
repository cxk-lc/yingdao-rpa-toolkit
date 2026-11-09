# -*- coding: utf-8 -*-
"""app list / app runs：请求构造、分页与游标。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yingdao_rpa.client import ApiMeta
from yingdao_rpa.commands.app import (
    APP_LIST_PATH,
    APP_RUN_LIST_PATH,
    build_list_body,
    build_runs_body,
    run_list,
    run_runs,
)
from yingdao_rpa.config import Config
from yingdao_rpa.errors import ParamError
from yingdao_rpa.runtime import Runtime

APP_A = {
    "appId": "app-1",
    "appName": "应用A",
    "appType": "app",
    "appTypeName": "应用",
    "ownerName": "张三",
    "ownerAccount": "zhangsan@corp",
    "version": "1",
    "supportParam": True,
    "updateTime": "2026-01-01 10:00:00",
}
APP_B = {**APP_A, "appId": "app-2", "appName": "应用B"}
RUN_A = {
    "id": 100,
    "runRecordId": "r-100",
    "appId": "app-1",
    "appName": "应用A",
    "userName": "u@corp",
    "startTime": "2026-01-01 10:00:00",
    "endTime": "2026-01-01 10:00:01",
    "runStatus": "finish",
    "runStatusName": "完成",
    "runningTime": 1,
    "startMode": "manual",
    "startModeName": "手工执行",
}
RUN_B = {**RUN_A, "id": 99, "runRecordId": "r-99"}
RUN_C = {**RUN_A, "id": 98, "runRecordId": "r-98"}


def page_payload(rows, page=1, pages=1, size=30, total=None):
    return {
        "success": True,
        "code": 200,
        "data": rows,
        "page": {
            "total": total if total is not None else len(rows),
            "size": size,
            "page": page,
            "pages": pages,
            "offset": (page - 1) * size,
        },
    }


class FakeClient:
    def __init__(self, list_payloads=None, run_payloads=None):
        self.queues = {
            APP_LIST_PATH: list(list_payloads or []),
            APP_RUN_LIST_PATH: list(run_payloads or []),
        }
        self.calls: list[dict] = []
        self.last_meta = ApiMeta(base_url="https://example.test", api_code=200, api_success=True)

    def request(self, method, path, body=None, **kwargs):
        self.calls.append({"method": method, "path": path, "body": body})
        queue = self.queues[path]
        if not queue:
            raise AssertionError(f"没有为 {path} 准备响应")
        return queue.pop(0) if len(queue) > 1 else queue[0]

    def preview(self, method, path, body=None, **kwargs):
        return {"method": method, "url": "https://example.test" + path, "body": body}


def runtime(client=None, dry_run=False):
    return Runtime(
        config=Config(
            base_url="https://example.test",
            access_key_id="ak",
            access_key_secret="sk",
        ),
        client=client or FakeClient(),
        dry_run=dry_run,
    )


def list_args(**overrides):
    base = {
        "app_id": None,
        "app_name": None,
        "owner": None,
        "page": None,
        "size": None,
        "all": False,
        "max_pages": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def runs_args(**overrides):
    base = {
        "app_id": None,
        "begin_date": None,
        "end_date": None,
        "min_id": None,
        "size": None,
        "all": False,
        "max_pages": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_list_body_defaults_to_first_page():
    body, page, size = build_list_body(list_args())

    assert body == {"page": "1", "size": "30"}
    assert (page, size) == (1, 30)


def test_list_body_includes_filters():
    body, _, _ = build_list_body(
        list_args(app_id=" app-1 ", app_name=" 应用 ", owner=" owner@corp ", page=2, size=100)
    )

    assert body == {
        "page": "2",
        "size": "100",
        "appId": "app-1",
        "appName": "应用",
        "ownerUserSearchKey": "owner@corp",
    }


@pytest.mark.parametrize(("page", "size"), [(0, 30), (1, 0), (1, 101)])
def test_list_rejects_invalid_page_or_size(page, size):
    with pytest.raises(ParamError):
        build_list_body(list_args(page=page, size=size))


def test_list_single_page():
    client = FakeClient(list_payloads=[page_payload([APP_A, APP_B])])

    result = run_list(list_args(), runtime(client))

    assert result["data"]["kind"] == "app_list"
    assert result["data"]["count"] == 2
    assert client.calls[0]["body"]["page"] == "1"


def test_list_all_aggregates_pages():
    client = FakeClient(
        list_payloads=[
            page_payload([APP_A, APP_B], page=1, pages=2, size=2, total=3),
            page_payload([{**APP_A, "appId": "app-3"}], page=2, pages=2, size=2, total=3),
        ]
    )

    result = run_list(list_args(all=True, size=2), runtime(client))

    assert result["data"]["count"] == 3
    assert [call["body"]["page"] for call in client.calls] == ["1", "2"]
    assert result["data"]["requested"]["fetchedPages"] == 2


def test_list_max_pages_stops_with_warning():
    client = FakeClient(
        list_payloads=[page_payload([APP_A, APP_B], page=1, pages=5, size=2, total=10)]
    )

    result = run_list(list_args(all=True, size=2, max_pages=1), runtime(client))

    assert result["data"]["count"] == 2
    assert result["warnings"] and "max-pages" in result["warnings"][0]


def test_runs_require_app_or_time():
    with pytest.raises(ParamError, match="至少一个"):
        build_runs_body(runs_args())


def test_runs_time_only_requires_both_bounds():
    with pytest.raises(ParamError, match="同时提供"):
        build_runs_body(runs_args(begin_date="2026-01-01"))


def test_runs_body_normalizes_dates_and_cursor():
    body, min_id, size = build_runs_body(
        runs_args(app_id="app-1", begin_date="2026-01-01", end_date="2026-01-02 12:30:00")
    )

    assert body == {
        "size": "30",
        "minId": 0,
        "appId": "app-1",
        "beginDate": "2026-01-01 00:00:00",
        "endDate": "2026-01-02 12:30:00",
    }
    assert (min_id, size) == (0, 30)


def test_runs_reject_reversed_time_range():
    with pytest.raises(ParamError, match="不能晚于"):
        build_runs_body(runs_args(begin_date="2026-02-01", end_date="2026-01-01"))


def test_runs_reject_range_over_seven_days():
    with pytest.raises(ParamError, match="7 天"):
        build_runs_body(runs_args(begin_date="2026-01-01", end_date="2026-01-09"))


def test_runs_allow_seven_day_range():
    body, _, _ = build_runs_body(
        runs_args(begin_date="2026-01-01", end_date="2026-01-08")
    )

    assert body["beginDate"] == "2026-01-01 00:00:00"
    assert body["endDate"] == "2026-01-08 00:00:00"


def test_runs_single_page_sets_next_min_id():
    client = FakeClient(run_payloads=[page_payload([RUN_A, RUN_B])])

    result = run_runs(runs_args(app_id="app-1"), runtime(client))

    assert result["data"]["kind"] == "app_run_list"
    assert result["data"]["count"] == 2
    assert result["data"]["nextMinId"] == 100
    assert result["data"]["items"][0]["statusName"] == "完成"
    assert client.calls[0]["body"]["minId"] == 0


def test_runs_all_follows_min_id_and_dedupes():
    client = FakeClient(
        run_payloads=[
            page_payload([RUN_A, RUN_B], page=1, pages=2, size=2, total=3),
            page_payload([RUN_B, RUN_C], page=2, pages=2, size=2, total=3),
        ]
    )

    result = run_runs(runs_args(app_id="app-1", all=True, size=2), runtime(client))

    assert [call["body"]["minId"] for call in client.calls] == [0, 100]
    assert result["data"]["count"] == 3
    assert result["data"]["nextMinId"] == 99
    assert result["data"]["requested"]["fetchedPages"] == 2


def test_runs_max_pages_stops_with_warning():
    client = FakeClient(
        run_payloads=[page_payload([RUN_A, RUN_B], page=1, pages=5, size=2, total=10)]
    )

    result = run_runs(
        runs_args(app_id="app-1", all=True, size=2, max_pages=1), runtime(client)
    )

    assert result["data"]["count"] == 2
    assert result["warnings"] and "max-pages" in result["warnings"][0]


def test_runs_dry_run_does_not_send_request():
    client = FakeClient()

    result = run_runs(runs_args(app_id="app-1"), runtime(client, dry_run=True))

    assert client.calls == []
    assert result["data"]["request"]["body"]["appId"] == "app-1"
    assert result["data"]["request"]["body"]["minId"] == 0
