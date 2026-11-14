# -*- coding: utf-8 -*-
"""job start 与机器人调度规则的集成。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yingdao_rpa.client import ApiMeta
from yingdao_rpa.commands.job import START_PATH, run_start
from yingdao_rpa.config import Config
from yingdao_rpa.errors import ParamError, PreconditionError
from yingdao_rpa.runtime import Runtime
from yingdao_rpa.scheduling import JOB_LIST_PATH, ROBOT_LIST_PATH, ROBOT_QUERY_PATH

IDLE_A = {"robotClientUuid": "r-a", "robotClientName": "a@corp", "status": "idle"}
IDLE_B = {"robotClientUuid": "r-b", "robotClientName": "b@corp", "status": "idle"}
BUSY = {"robotClientUuid": "r-busy", "robotClientName": "busy@corp", "status": "running"}


def page(rows):
    return {
        "success": True,
        "code": 200,
        "data": rows,
        "page": {"total": len(rows), "size": 100, "page": 1, "pages": 1},
    }


def history(rows):
    return {
        "success": True,
        "code": 200,
        "data": {
            "hasData": False,
            "nextId": None,
            "preId": None,
            "cursorDirection": "next",
            "dataList": rows,
        },
    }


def finish(uuid, name):
    return {"robotClientUuid": uuid, "robotClientName": name, "status": "finish"}


class FakeClient:
    def __init__(self, *, robots=None, idle=None, robot_map=None, history_rows=None):
        self.robots = list(robots or [])
        self.idle = list(idle or [])
        self.robot_map = dict(robot_map or {})
        self.history_rows = list(history_rows or [])
        self.calls: list[dict] = []
        self.start_body = None
        self.last_meta = ApiMeta(base_url="https://example.test", api_code=200, api_success=True)

    def request(self, method, path, body=None, **kwargs):
        self.calls.append({"path": path, "body": body})
        if path == ROBOT_QUERY_PATH:
            robot = self.robot_map.get((body or {}).get("accountName"))
            return {"success": True, "code": 200, "data": robot}
        if path == ROBOT_LIST_PATH:
            return page(self.idle if (body or {}).get("status") == "idle" else self.robots)
        if path == JOB_LIST_PATH:
            return history(self.history_rows)
        if path == START_PATH:
            self.start_body = body
            return {
                "success": True,
                "code": 200,
                "data": {"jobUuid": "job-1", "idempotentFlag": False},
                "requestId": "req-1",
            }
        raise AssertionError(f"未预期路径 {path}")

    def preview(self, method, path, body=None, **kwargs):
        return {"method": method, "url": "https://example.test" + path, "body": body}


def runtime(client, dry_run=False):
    return Runtime(
        config=Config(base_url="https://example.test", access_key_id="ak", access_key_secret="sk"),
        client=client,
        dry_run=dry_run,
    )


def args(**overrides):
    base = {
        "app_id": "app-1",
        "account_name": None,
        "robot_group_uuid": None,
        "auto_robot": False,
        "queue_if_busy": False,
        "param": [],
        "params_file": None,
        "idempotent_uuid": None,
        "priority": None,
        "wait_timeout_seconds": None,
        "run_timeout": None,
        "execute_scope": None,
        "wait": False,
        "interval": None,
        "max_wait": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_auto_robot_dry_run_previews_lookup_and_start():
    client = FakeClient(idle=[IDLE_A])

    result = run_start(args(auto_robot=True), runtime(client, dry_run=True))

    assert client.calls == []
    data = result["data"]
    assert data["resolution"] == "auto-robot"
    assert data["request"]["url"].endswith(ROBOT_LIST_PATH)
    assert data["followup"]["body"]["accountName"] == "<selected-account>"


def test_auto_robot_rejects_explicit_account():
    with pytest.raises(ParamError, match="不能与"):
        run_start(args(auto_robot=True, account_name="a@corp"), runtime(FakeClient(), dry_run=True))


def test_auto_robot_starts_with_most_successful_idle():
    client = FakeClient(
        idle=[IDLE_A, IDLE_B],
        history_rows=[finish("r-a", "a@corp"), finish("r-a", "a@corp"), finish("r-b", "b@corp")],
    )

    result = run_start(args(auto_robot=True), runtime(client))

    assert client.start_body["accountName"] == "a@corp"
    assert result["data"]["dispatch"]["reason"] == "auto_most_success"
    assert result["data"]["dispatch"]["successCount"] == 2
    assert result["data"]["jobUuid"] == "job-1"


def test_no_target_defaults_to_auto_selection():
    client = FakeClient(idle=[IDLE_A], history_rows=[])

    result = run_start(args(), runtime(client))

    assert client.start_body["accountName"] == "a@corp"
    assert result["data"]["dispatch"]["reason"] == "auto_only_idle"


def test_specified_busy_robot_returns_decision_before_start():
    client = FakeClient(robot_map={"busy@corp": BUSY}, idle=[IDLE_A])

    with pytest.raises(PreconditionError) as excinfo:
        run_start(args(account_name="busy@corp"), runtime(client))

    assert excinfo.value.data["reason"] == "specified_robot_busy"
    assert [item["accountName"] for item in excinfo.value.data["idleCandidates"]] == ["a@corp"]
    assert not any(call["path"] == START_PATH for call in client.calls)


def test_queue_if_busy_starts_on_busy_robot():
    client = FakeClient(robot_map={"busy@corp": BUSY})

    result = run_start(
        args(account_name="busy@corp", queue_if_busy=True),
        runtime(client),
    )

    assert client.start_body["accountName"] == "busy@corp"
    assert result["data"]["dispatch"]["reason"] == "specified_queue"


def test_queue_if_busy_with_group_is_rejected():
    with pytest.raises(ParamError, match="queue-if-busy"):
        run_start(
            args(robot_group_uuid="group-1", queue_if_busy=True),
            runtime(FakeClient(), dry_run=True),
        )
