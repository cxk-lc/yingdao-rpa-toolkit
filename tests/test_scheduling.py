# -*- coding: utf-8 -*-
"""机器人调度规则：指定优先、忙碌决策、空闲成功率选择。"""

from __future__ import annotations

import pytest

from yingdao_rpa.client import ApiMeta
from yingdao_rpa.errors import ApiError, PreconditionError
from yingdao_rpa.scheduling import (
    JOB_LIST_PATH,
    ROBOT_LIST_PATH,
    ROBOT_QUERY_PATH,
    list_robots,
    select_robot,
)

IDLE_A = {
    "robotClientUuid": "r-a",
    "robotClientName": "a@corp",
    "status": "idle",
    "description": "A",
}
IDLE_B = {
    "robotClientUuid": "r-b",
    "robotClientName": "b@corp",
    "status": "idle",
    "description": "B",
}
BUSY = {
    "robotClientUuid": "r-busy",
    "robotClientName": "busy@corp",
    "status": "running",
    "description": "运行中",
}


def page(rows, pages=1, size=100):
    return {
        "success": True,
        "code": 200,
        "data": rows,
        "page": {"total": len(rows), "size": size, "page": 1, "pages": pages},
    }


def history(rows, has_data=False, next_id=None):
    return {
        "success": True,
        "code": 200,
        "data": {
            "hasData": has_data,
            "nextId": next_id,
            "preId": None,
            "cursorDirection": "next",
            "dataList": rows,
        },
    }


def finish(r_uuid, r_name):
    return {"robotClientUuid": r_uuid, "robotClientName": r_name, "status": "finish"}


class FakeClient:
    def __init__(
        self,
        *,
        robots=None,
        idle=None,
        robot_map=None,
        history_payloads=None,
        history_error: Exception | None = None,
    ):
        self.robots = list(robots or [])
        self.idle = list(idle if idle is not None else [])
        self.robot_map = dict(robot_map or {})
        self.history_payloads = list(history_payloads or [history([])])
        self.history_error = history_error
        self.calls: list[dict] = []
        self.last_meta = ApiMeta(base_url="https://example.test", api_code=200, api_success=True)

    def request(self, method, path, body=None, **kwargs):
        self.calls.append({"path": path, "body": body})
        if path == ROBOT_QUERY_PATH:
            name = (body or {}).get("accountName")
            robot = self.robot_map.get(name)
            if not robot:
                raise ApiError("参数错误， 未查询到机器人", code=400)
            return {"success": True, "code": 200, "data": robot}
        if path == ROBOT_LIST_PATH:
            if (body or {}).get("status") == "idle":
                return page(self.idle)
            return page(self.robots)
        if path == JOB_LIST_PATH:
            if self.history_error:
                raise self.history_error
            if not self.history_payloads:
                return history([])
            return self.history_payloads.pop(0) if len(self.history_payloads) > 1 else self.history_payloads[0]
        raise AssertionError(f"未预期路径 {path}")


def test_specified_idle_robot_is_used_directly():
    client = FakeClient(robot_map={"a@corp": IDLE_A})

    selection = select_robot(client, "app-1", account_name="a@corp")

    assert selection["reason"] == "specified_idle"
    assert selection["accountName"] == "a@corp"
    assert [call["path"] for call in client.calls] == [ROBOT_QUERY_PATH]


def test_specified_busy_robot_returns_decision_with_candidates():
    client = FakeClient(
        robot_map={"busy@corp": BUSY},
        idle=[IDLE_B, IDLE_A],
        history_payloads=[
            history(
                [
                    finish("r-a", "a@corp"),
                    finish("r-a", "a@corp"),
                    finish("r-b", "b@corp"),
                ]
            )
        ],
    )

    with pytest.raises(PreconditionError) as excinfo:
        select_robot(client, "app-1", account_name="busy@corp")

    data = excinfo.value.data
    assert data["reason"] == "specified_robot_busy"
    assert data["requestedRobot"]["accountName"] == "busy@corp"
    assert [item["accountName"] for item in data["idleCandidates"]] == ["a@corp", "b@corp"]
    assert data["idleCandidates"][0]["successCount"] == 2
    assert data["queueOption"]["flag"] == "--queue-if-busy"


def test_specified_busy_with_queue_flag_accepts_queue():
    offline = {**BUSY, "status": "offline", "robotClientName": "off@corp"}
    client = FakeClient(robot_map={"off@corp": offline})

    selection = select_robot(
        client, "app-1", account_name="off@corp", queue_if_busy=True
    )

    assert selection["reason"] == "specified_queue"
    assert selection["accountName"] == "off@corp"
    assert selection["warnings"]


def test_auto_prefers_most_successful_idle_robot():
    client = FakeClient(
        idle=[IDLE_A, IDLE_B],
        history_payloads=[
            history(
                [
                    finish("r-a", "a@corp"),
                    finish("r-a", "a@corp"),
                    finish("r-b", "b@corp"),
                ]
            )
        ],
    )

    selection = select_robot(client, "app-1")

    assert selection["reason"] == "auto_most_success"
    assert selection["accountName"] == "a@corp"
    assert selection["successCount"] == 2


def test_auto_random_when_no_success_history():
    client = FakeClient(idle=[IDLE_A, IDLE_B], history_payloads=[history([])])
    picked = []

    def chooser(pool):
        picked.extend(item["accountName"] for item in pool)
        return pool[-1]

    selection = select_robot(client, "app-1", chooser=chooser)

    assert selection["reason"] == "auto_random"
    assert selection["accountName"] == "b@corp"
    assert sorted(picked) == ["a@corp", "b@corp"]


def test_auto_single_idle_does_not_randomize():
    client = FakeClient(idle=[IDLE_A], history_payloads=[history([])])

    selection = select_robot(client, "app-1")

    assert selection["reason"] == "auto_only_idle"
    assert selection["accountName"] == "a@corp"


def test_auto_without_idle_returns_online_candidates():
    client = FakeClient(
        robots=[BUSY, {**IDLE_A, "status": "offline"}],
        idle=[],
        history_payloads=[history([finish("r-busy", "busy@corp")])],
    )

    with pytest.raises(PreconditionError) as excinfo:
        select_robot(client, "app-1")

    data = excinfo.value.data
    assert data["reason"] == "no_idle_robot"
    assert [item["accountName"] for item in data["onlineCandidates"]] == ["busy@corp"]


def test_auto_without_any_online_robot_reports_no_available():
    client = FakeClient(robots=[{**IDLE_A, "status": "offline"}], idle=[])

    with pytest.raises(PreconditionError) as excinfo:
        select_robot(client, "app-1")

    assert excinfo.value.data["reason"] == "no_available_robot"


def test_history_failure_falls_back_to_random_idle():
    client = FakeClient(
        idle=[IDLE_A, IDLE_B],
        history_error=ApiError("历史接口无权限", code=403),
    )

    selection = select_robot(client, "app-1", chooser=lambda pool: pool[0])

    assert selection["reason"] == "auto_random"
    assert selection["warnings"]


def test_list_robots_paginates():
    client = FakeClient(robots=[IDLE_A])
    # 覆盖 list_robots 的分页判断：两页，第一页返回 1 条
    client.request = lambda method, path, body=None, **kwargs: (
        page([IDLE_A], pages=2, size=1)
        if (body or {}).get("page") == 1
        else page([IDLE_B], pages=2, size=1)
    )

    robots = list_robots(client, page_size=1)

    assert [robot["accountName"] for robot in robots] == ["a@corp", "b@corp"]
