# -*- coding: utf-8 -*-
"""robot info：账号名补全、请求体与状态呈现。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yingdao_rpa.client import ApiMeta
from yingdao_rpa.commands.robot import run_info
from yingdao_rpa.config import Config
from yingdao_rpa.errors import ApiError, ParamError
from yingdao_rpa.runtime import Runtime

ROBOT = {
    "robotClientUuid": "0d6a835a-2e08-414a-af73-1e43f9d9c8ff",
    "robotClientName": "ceshi1@csqy1",
    "status": "idle",
    "description": "ceshi1",
    "clientIp": "172.16.28.156",
    "remark": "运行成功",
}


class FakeClient:
    def __init__(self, payload=None):
        self.payload = payload or {"success": True, "code": 200, "data": dict(ROBOT)}
        self.calls: list[dict] = []
        self.last_meta = ApiMeta(
            base_url="https://example.test", api_code=200, api_success=True, request_id="req-1"
        )

    def preview(self, method, path, body=None, **kwargs):
        return {"method": method, "url": "https://example.test" + path, "body": body}

    def request(self, method, path, body=None, **kwargs):
        self.calls.append({"method": method, "path": path, "body": body})
        return self.payload


def make_runtime(suffix: str = "@csqy1", dry_run: bool = False, client=None) -> Runtime:
    return Runtime(
        config=Config(
            base_url="https://example.test",
            access_key_id="ak",
            access_key_secret="sk",
            enterprise_suffix=suffix,
        ),
        client=client or FakeClient(),
        dry_run=dry_run,
    )


def args(**overrides) -> SimpleNamespace:
    base = {"name": None, "uuid": None, "suffix": None}
    base.update(overrides)
    return SimpleNamespace(**base)


def test_name_without_suffix_uses_config():
    runtime = make_runtime()

    result = run_info(args(name="ceshi1"), runtime)

    assert runtime.client.calls[0]["body"] == {"accountName": "ceshi1@csqy1"}
    assert result["data"]["requested"]["suffixApplied"] is True


def test_full_name_is_not_overwritten():
    runtime = make_runtime()

    run_info(args(name="ceshi1@other"), runtime)

    assert runtime.client.calls[0]["body"] == {"accountName": "ceshi1@other"}


def test_command_suffix_overrides_config():
    runtime = make_runtime(suffix="@config-suffix")

    run_info(args(name="ceshi1", suffix="@cli-suffix"), runtime)

    assert runtime.client.calls[0]["body"] == {"accountName": "ceshi1@cli-suffix"}


def test_missing_suffix_everywhere_is_blocked():
    runtime = make_runtime(suffix="")

    with pytest.raises(ParamError, match="缺少企业账号后缀") as excinfo:
        run_info(args(name="ceshi1"), runtime)

    assert "enterpriseSuffix" in (excinfo.value.hint or "")
    assert runtime.client.calls == []


def test_uuid_query_skips_account_name():
    runtime = make_runtime()

    run_info(args(uuid="robot-uuid-1"), runtime)

    assert runtime.client.calls[0]["body"] == {"robotClientUuid": "robot-uuid-1"}


def test_suffix_with_uuid_is_rejected():
    runtime = make_runtime()

    with pytest.raises(ParamError, match="--suffix"):
        run_info(args(uuid="robot-uuid-1", suffix="@csqy1"), runtime)


def test_dry_run_does_not_send_request():
    runtime = make_runtime(dry_run=True)

    result = run_info(args(name="ceshi1"), runtime)

    assert runtime.client.calls == []
    assert result["data"]["kind"] == "request_preview"
    assert result["data"]["request"]["body"] == {"accountName": "ceshi1@csqy1"}


def test_status_is_translated_and_derived():
    result = run_info(args(name="ceshi1"), make_runtime())
    robot = result["data"]["robot"]

    assert robot["statusName"] == "空闲"
    assert robot["online"] is True
    assert robot["idle"] is True


def test_offline_status_is_derived():
    client = FakeClient({"success": True, "code": 200, "data": {**ROBOT, "status": "offline"}})
    result = run_info(args(name="ceshi1"), make_runtime(client=client))
    robot = result["data"]["robot"]

    assert robot["statusName"] == "离线"
    assert robot["online"] is False
    assert robot["idle"] is False


def test_empty_data_means_not_found():
    client = FakeClient({"success": True, "code": 200, "data": None})

    with pytest.raises(ApiError, match="未查询到机器人"):
        run_info(args(name="ceshi1"), make_runtime(client=client))


def test_not_found_api_error_adds_suffix_hint():
    class ErrorClient(FakeClient):
        def request(self, method, path, body=None, **kwargs):
            raise ApiError("参数错误， 未查询到机器人", code=400, request_id="req-2")

    with pytest.raises(ApiError) as excinfo:
        run_info(args(name="ceshi1"), make_runtime(client=ErrorClient()))

    assert "enterpriseSuffix" in (excinfo.value.hint or "")
    assert excinfo.value.request_id == "req-2"
