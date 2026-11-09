# -*- coding: utf-8 -*-
"""robot tasks：任务队列/历史记录的过滤、游标翻页与状态呈现。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yingdao_rpa.client import ApiMeta
from yingdao_rpa.commands.robot import TASK_LIST_PATH, build_tasks_body, run_tasks
from yingdao_rpa.config import Config
from yingdao_rpa.errors import ParamError
from yingdao_rpa.runtime import Runtime

TASK_A = {
    "id": 100,
    "jobUuid": "job-100",
    "taskName": "任务A",
    "status": "error",
    "triggerTime": "2026-01-01 10:00:00",
    "startTime": "2026-01-01 10:00:01",
    "endTime": "2026-01-01 10:00:02",
    "robotUuid": "app-1",
    "robotName": "应用A",
    "remark": "元素未找到",
    "robotClientUuid": "rc-1",
    "robotClientName": "机器人1",
}
TASK_B = {**TASK_A, "id": 99, "jobUuid": "job-99", "taskName": "任务B", "status": "finish", "remark": ""}
TASK_C = {**TASK_A, "id": 98, "jobUuid": "job-98", "taskName": "任务C", "status": "running", "remark": ""}


def task_payload(rows, *, has_data=True, next_id=100, pre_id=105, direction="next"):
    return {
        "success": True,
        "code": 200,
        "data": {
            "hasData": has_data,
            "nextId": next_id,
            "preId": pre_id,
            "cursorDirection": direction,
            "dataList": rows,
        },
    }


class FakeClient:
    def __init__(self, payloads=None):
        self.payloads = list(payloads or [])
        self.calls: list[dict] = []
        self.last_meta = ApiMeta(base_url="https://example.test", api_code=200, api_success=True)

    def request(self, method, path, body=None, **kwargs):
        self.calls.append({"method": method, "path": path, "body": body})
        if not self.payloads:
            raise AssertionError("没有准备响应")
        return self.payloads.pop(0) if len(self.payloads) > 1 else self.payloads[0]

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


def args(**overrides):
    base = {
        "app_id": None,
        "robot_client_uuid": None,
        "schedule_uuid": None,
        "status": None,
        "trigger_begin": None,
        "trigger_end": None,
        "cursor_id": None,
        "direction": None,
        "size": None,
        "all": False,
        "max_pages": None,
        "query_api": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_body_defaults():
    body, size, direction = build_tasks_body(args())

    assert body == {"cursorDirection": "next", "size": 20}
    assert (size, direction) == (20, "next")


def test_body_includes_filters():
    body, _, direction = build_tasks_body(
        args(
            app_id=" app-1 ",
            robot_client_uuid=" rc-1 ",
            schedule_uuid=" sch-1 ",
            status=["error,finish", "error"],
            trigger_begin="2026-01-01",
            trigger_end="2026-01-02 12:30:00",
            cursor_id=200,
            direction="pre",
            size=100,
            query_api=True,
        )
    )

    assert direction == "pre"
    assert body == {
        "cursorDirection": "pre",
        "size": 100,
        "robotUuid": "app-1",
        "robotClientUuid": "rc-1",
        "scheduleUuid": "sch-1",
        "statusList": ["error", "finish"],
        "triggerTimeBegin": "2026-01-01 00:00:00",
        "triggerTimeEnd": "2026-01-02 12:30:00",
        "cursorId": 200,
        "queryApi": True,
    }


@pytest.mark.parametrize("size", [0, 101])
def test_invalid_size(size):
    with pytest.raises(ParamError):
        build_tasks_body(args(size=size))


def test_invalid_max_pages():
    with pytest.raises(ParamError):
        run_tasks(args(max_pages=0), runtime())


def test_unknown_status_is_rejected():
    with pytest.raises(ParamError, match="未知运行状态"):
        build_tasks_body(args(status=["vip"]))


def test_pre_direction_requires_cursor():
    with pytest.raises(ParamError, match="--cursor-id"):
        build_tasks_body(args(direction="pre"))


def test_reversed_trigger_time_is_rejected():
    with pytest.raises(ParamError, match="不能晚于"):
        build_tasks_body(args(trigger_begin="2026-02-01", trigger_end="2026-01-01"))


def test_single_page_adds_status_name():
    client = FakeClient([task_payload([TASK_A, TASK_B])])

    result = run_tasks(args(app_id="app-1"), runtime(client))

    assert result["data"]["kind"] == "robot_task_list"
    assert result["data"]["count"] == 2
    assert result["data"]["items"][0]["statusName"] == "异常"
    assert result["data"]["items"][1]["statusName"] == "完成"
    assert client.calls[0]["body"]["robotUuid"] == "app-1"


def test_all_follows_next_cursor():
    client = FakeClient(
        [
            task_payload([TASK_A, TASK_B], has_data=True, next_id=100),
            task_payload([TASK_C], has_data=False, next_id=50),
        ]
    )

    result = run_tasks(args(all=True, size=2), runtime(client))

    assert [call["body"].get("cursorId") for call in client.calls] == [None, 100]
    assert result["data"]["count"] == 3
    assert result["data"]["cursor"]["hasData"] is False
    assert result["data"]["requested"]["fetchedPages"] == 2
    assert result["warnings"] == []


def test_all_stops_when_has_data_false():
    client = FakeClient([task_payload([TASK_A], has_data=False)])

    result = run_tasks(args(all=True, size=20), runtime(client))

    assert result["data"]["count"] == 1
    assert len(client.calls) == 1


def test_all_stops_when_cursor_does_not_advance():
    client = FakeClient(
        [
            task_payload([TASK_A], has_data=True, next_id=100),
            task_payload([TASK_A], has_data=True, next_id=100),
        ]
    )

    result = run_tasks(args(all=True, size=1), runtime(client))

    assert result["data"]["count"] == 1
    assert result["warnings"] and "游标" in result["warnings"][0]


def test_all_stops_at_max_pages():
    client = FakeClient([task_payload([TASK_A, TASK_B], has_data=True, next_id=100)])

    result = run_tasks(args(all=True, size=2, max_pages=1), runtime(client))

    assert result["data"]["count"] == 2
    assert result["warnings"] and "max-pages" in result["warnings"][0]


def test_dry_run_does_not_send_request():
    client = FakeClient([])

    result = run_tasks(args(app_id="app-1", query_api=True), runtime(client, dry_run=True))

    assert client.calls == []
    assert result["data"]["request"]["body"]["queryApi"] is True
    assert result["data"]["request"]["body"]["cursorDirection"] == "next"
