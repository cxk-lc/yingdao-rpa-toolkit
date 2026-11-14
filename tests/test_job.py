# -*- coding: utf-8 -*-
"""job 命令：参数解析、请求体构造、轮询与失败判定。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yingdao_rpa.config import Config
from yingdao_rpa.commands.job import (
    _parse_param,
    _poll_settings,
    _split_failure,
    build_start_body,
    poll_job,
)
from yingdao_rpa.errors import JobFailedError, ParamError, PollTimeoutError

CONFIG = Config(access_key_id="ak", access_key_secret="sk", default_account_name="")


def args(**overrides) -> SimpleNamespace:
    base = {
        "app_id": "app-1",
        "account_name": "robot@corp",
        "robot_group_uuid": None,
        "param": [],
        "params_file": None,
        "idempotent_uuid": None,
        "priority": None,
        "wait_timeout_seconds": None,
        "run_timeout": None,
        "execute_scope": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_parse_param_defaults_to_str():
    assert _parse_param("月份=2026-10") == {"name": "月份", "value": "2026-10", "type": "str"}


def test_parse_param_supports_type_suffix():
    assert _parse_param("页数=10:int") == {"name": "页数", "value": "10", "type": "int"}


def test_parse_param_keeps_url_colon():
    parsed = _parse_param("回调=https://example.com/a")
    assert parsed["value"] == "https://example.com/a"
    assert parsed["type"] == "str"


def test_parse_param_requires_name_and_value():
    with pytest.raises(ParamError):
        _parse_param("没有等号")
    with pytest.raises(ParamError):
        _parse_param("=值")


def test_build_start_body_minimal():
    body = build_start_body(args(), CONFIG)

    assert body == {"robotUuid": "app-1", "accountName": "robot@corp"}


def test_build_start_body_with_optional_fields():
    body = build_start_body(
        args(
            idempotent_uuid="idem-1",
            priority="high",
            wait_timeout_seconds=600,
            run_timeout=1200,
            execute_scope="any",
            param=["月份=2026-10", "页数=10:int"],
        ),
        CONFIG,
    )

    assert body["idempotentUuid"] == "idem-1"
    assert body["priority"] == "high"
    assert body["waitTimeoutSeconds"] == 600
    assert body["runTimeout"] == 1200
    assert body["executeScope"] == "any"
    assert body["params"] == [
        {"name": "月份", "value": "2026-10", "type": "str"},
        {"name": "页数", "value": "10", "type": "int"},
    ]


def test_account_and_group_are_mutually_exclusive():
    with pytest.raises(ParamError, match="互斥"):
        build_start_body(args(robot_group_uuid="group-1"), CONFIG)


def test_explicit_account_overrides_config_group():
    config = Config(
        access_key_id="ak",
        access_key_secret="sk",
        default_robot_client_group_uuid="group-from-config",
    )

    body = build_start_body(args(account_name="robot@corp"), config)

    assert body["accountName"] == "robot@corp"
    assert "robotClientGroupUuid" not in body


def test_missing_target_leaves_account_for_auto_selection():
    body = build_start_body(args(account_name=None), CONFIG)

    assert "accountName" not in body
    assert "robotClientGroupUuid" not in body


def test_default_account_from_config_is_used():
    config = Config(access_key_id="ak", access_key_secret="sk", default_account_name="default@corp")

    body = build_start_body(args(account_name=None), config)

    assert body["accountName"] == "default@corp"


def test_duplicate_param_names_rejected():
    with pytest.raises(ParamError, match="重复"):
        build_start_body(args(param=["a=1", "a=2"]), CONFIG)


def test_param_length_limit():
    with pytest.raises(ParamError, match="超过"):
        build_start_body(args(param=["big=" + "x" * 9000]), CONFIG)


def test_wait_timeout_range():
    with pytest.raises(ParamError, match="wait-timeout-seconds"):
        build_start_body(args(wait_timeout_seconds=10), CONFIG)


def test_idempotent_uuid_length_limit():
    with pytest.raises(ParamError, match="36"):
        build_start_body(args(idempotent_uuid="x" * 37), CONFIG)


def test_poll_settings_use_config_defaults():
    config = Config(poll_interval_seconds=15, max_poll_seconds=120)
    interval, max_wait = _poll_settings(SimpleNamespace(interval=None, max_wait=None), config)

    assert (interval, max_wait) == (15, 120)


@pytest.mark.parametrize(
    ("interval", "max_wait"),
    [(1, None), (None, 0), (-5, 60)],
)
def test_poll_settings_reject_invalid_values(interval, max_wait):
    with pytest.raises(ParamError):
        _poll_settings(SimpleNamespace(interval=interval, max_wait=max_wait), CONFIG)


class FakeClient:
    def __init__(self, jobs):
        self.jobs = list(jobs)
        self.calls = 0

    def request(self, method, path, body=None, **kwargs):
        self.calls += 1
        return {"success": True, "code": 200, "data": self.jobs.pop(0)}


def test_poll_until_finish():
    client = FakeClient([{"status": "waiting"}, {"status": "running"}, {"status": "finish"}])
    sleeps: list[float] = []

    job = poll_job(client, "j-1", interval=5, max_wait=60, sleep=sleeps.append)

    assert job["status"] == "finish"
    assert client.calls == 3
    assert sleeps == [5, 5]


def test_poll_timeout_keeps_last_status():
    client = FakeClient([{"status": "waiting"}])

    with pytest.raises(PollTimeoutError) as excinfo:
        poll_job(client, "j-1", interval=5, max_wait=0, sleep=lambda _: None)

    assert excinfo.value.data["job"]["status"] == "waiting"


def test_failed_terminal_status_raises_with_data():
    job = {"status": "error", "statusName": "异常", "remark": "元素未找到"}

    with pytest.raises(JobFailedError) as excinfo:
        _split_failure(job, "j-1")

    assert excinfo.value.data["jobUuid"] == "j-1"
    assert excinfo.value.data["job"]["remark"] == "元素未找到"


def test_finish_is_not_treated_as_failure():
    _split_failure({"status": "finish"}, "j-1")  # 不应抛异常
