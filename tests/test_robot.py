# -*- coding: utf-8 -*-
"""robot info：名称解析、企业账号补全、请求体与状态呈现。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yingdao_rpa.client import ApiMeta
from yingdao_rpa.commands.account import ACCOUNT_LIST_PATH
from yingdao_rpa.commands.robot import ROBOT_QUERY_PATH, run_info
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
ACCOUNT = {
    "userUuid": "u-1",
    "loginAccount": "ceshi1@csqy1",
    "name": "测试账号",
    "accountType": "basic",
}


def account_page(accounts):
    return {
        "success": True,
        "code": 200,
        "data": accounts,
        "page": {"total": len(accounts), "size": 100, "page": 1, "pages": 1},
    }


class FakeClient:
    def __init__(
        self,
        accounts=None,
        robot_payload=None,
        account_error: Exception | None = None,
        robot_error: Exception | None = None,
    ):
        self.accounts = list(accounts or [])
        self.robot_payload = robot_payload or {"success": True, "code": 200, "data": dict(ROBOT)}
        self.account_error = account_error
        self.robot_error = robot_error
        self.calls: list[dict] = []
        self.last_meta = ApiMeta(
            base_url="https://example.test", api_code=200, api_success=True, request_id="req-1"
        )

    def preview(self, method, path, query=None, body=None, **kwargs):
        return {
            "method": method,
            "url": "https://example.test" + path,
            "query": query,
            "body": body,
        }

    def request(self, method, path, query=None, body=None, **kwargs):
        self.calls.append({"method": method, "path": path, "query": query, "body": body})
        if path == ACCOUNT_LIST_PATH:
            if self.account_error:
                raise self.account_error
            return account_page(self.accounts)
        if path == ROBOT_QUERY_PATH:
            if self.robot_error:
                raise self.robot_error
            return self.robot_payload
        raise AssertionError(f"未预期的请求：{path}")


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


def robot_calls(client) -> list[dict]:
    return [call for call in client.calls if call["path"] == ROBOT_QUERY_PATH]


def test_full_name_is_kept_as_is():
    client = FakeClient()

    run_info(args(name="ceshi1@other"), make_runtime(client=client))

    assert robot_calls(client)[0]["body"] == {"accountName": "ceshi1@other"}
    assert len(client.calls) == 1


def test_explicit_suffix_skips_account_lookup():
    runtime = make_runtime(suffix="@config-suffix")

    result = run_info(args(name="ceshi1", suffix="@cli-suffix"), runtime)

    assert robot_calls(runtime.client)[0]["body"] == {"accountName": "ceshi1@cli-suffix"}
    assert len(runtime.client.calls) == 1
    assert result["data"]["requested"]["resolvedBy"] == "suffix"


def test_name_without_suffix_uses_login_account():
    client = FakeClient(accounts=[ACCOUNT])

    result = run_info(args(name="ceshi1"), make_runtime(client=client))

    assert client.calls[0]["path"] == ACCOUNT_LIST_PATH
    assert client.calls[0]["query"]["accountKeyword"] == "ceshi1"
    assert robot_calls(client)[0]["body"] == {"accountName": "ceshi1@csqy1"}
    assert result["data"]["requested"]["resolvedBy"] == "account"
    assert result["data"]["requested"]["lookup"]["matched"] == 1


def test_lookup_can_match_account_name_field():
    client = FakeClient(accounts=[{"loginAccount": "robot-01@corp", "name": "ceshi1"}])

    result = run_info(args(name="ceshi1"), make_runtime(client=client))

    assert robot_calls(client)[0]["body"] == {"accountName": "robot-01@corp"}
    assert result["data"]["requested"]["resolvedBy"] == "account"


def test_no_account_match_falls_back_to_config_suffix():
    client = FakeClient(accounts=[])
    runtime = make_runtime(suffix="@csqy1", client=client)

    result = run_info(args(name="ceshi1"), runtime)

    assert robot_calls(client)[0]["body"] == {"accountName": "ceshi1@csqy1"}
    assert result["data"]["requested"]["resolvedBy"] == "suffix"
    assert result["data"]["requested"]["fallback"] == "no-account-match"


def test_missing_suffix_everywhere_is_blocked():
    client = FakeClient(accounts=[])

    with pytest.raises(ParamError, match="未找到匹配的企业账号") as excinfo:
        run_info(args(name="ceshi1"), make_runtime(suffix="", client=client))

    assert "enterpriseSuffix" in (excinfo.value.hint or "")
    assert robot_calls(client) == []


def test_multiple_matches_are_rejected():
    client = FakeClient(
        accounts=[
            {"loginAccount": "ceshi1@a", "name": "A"},
            {"loginAccount": "ceshi1@b", "name": "B"},
        ]
    )

    with pytest.raises(ParamError, match="匹配到 2 个企业账号") as excinfo:
        run_info(args(name="ceshi1"), make_runtime(client=client))

    assert "ceshi1@a" in (excinfo.value.hint or "")
    assert "ceshi1@b" in (excinfo.value.hint or "")


def test_account_lookup_failure_falls_back_to_suffix():
    client = FakeClient(account_error=ApiError("企业账号接口无权限", code=403))
    runtime = make_runtime(suffix="@csqy1", client=client)

    result = run_info(args(name="ceshi1"), runtime)

    assert robot_calls(client)[0]["body"] == {"accountName": "ceshi1@csqy1"}
    assert result["data"]["requested"]["fallback"] == "account-query-failed"


def test_account_lookup_failure_without_suffix_propagates():
    client = FakeClient(account_error=ApiError("企业账号接口无权限", code=403))

    with pytest.raises(ApiError) as excinfo:
        run_info(args(name="ceshi1"), make_runtime(suffix="", client=client))

    assert "完整 loginAccount" in (excinfo.value.hint or "")


def test_uuid_query_skips_account_name_and_lookup():
    client = FakeClient()

    run_info(args(uuid="robot-uuid-1"), make_runtime(client=client))

    assert robot_calls(client)[0]["body"] == {"robotClientUuid": "robot-uuid-1"}
    assert len(client.calls) == 1


def test_suffix_with_uuid_is_rejected():
    runtime = make_runtime()

    with pytest.raises(ParamError, match="--suffix"):
        run_info(args(uuid="robot-uuid-1", suffix="@csqy1"), runtime)


def test_dry_run_without_suffix_shows_two_stage_preview():
    client = FakeClient()
    runtime = make_runtime(suffix="", dry_run=True, client=client)

    result = run_info(args(name="ceshi1"), runtime)

    assert client.calls == []
    data = result["data"]
    assert data["resolution"] == "account-lookup"
    assert data["request"]["url"].endswith(ACCOUNT_LIST_PATH)
    assert data["followup"]["body"] == {"accountName": "<loginAccount>"}
    assert "fallback" not in data


def test_dry_run_with_config_suffix_includes_fallback():
    client = FakeClient()
    runtime = make_runtime(suffix="@csqy1", dry_run=True, client=client)

    result = run_info(args(name="ceshi1"), runtime)

    assert result["data"]["resolution"] == "account-lookup"
    assert result["data"]["fallback"]["accountName"] == "ceshi1@csqy1"


def test_dry_run_with_explicit_suffix_previews_robot_query():
    client = FakeClient()
    runtime = make_runtime(suffix="@config", dry_run=True, client=client)

    result = run_info(args(name="ceshi1", suffix="@cli"), runtime)

    assert result["data"]["request"]["url"].endswith(ROBOT_QUERY_PATH)
    assert result["data"]["request"]["body"] == {"accountName": "ceshi1@cli"}


def test_status_is_translated_and_derived():
    result = run_info(args(name="ceshi1@corp"), make_runtime())
    robot = result["data"]["robot"]

    assert robot["statusName"] == "空闲"
    assert robot["online"] is True
    assert robot["idle"] is True


def test_offline_status_is_derived():
    client = FakeClient(
        robot_payload={"success": True, "code": 200, "data": {**ROBOT, "status": "offline"}}
    )
    result = run_info(args(name="ceshi1@corp"), make_runtime(client=client))
    robot = result["data"]["robot"]

    assert robot["statusName"] == "离线"
    assert robot["online"] is False
    assert robot["idle"] is False


def test_empty_data_means_not_found():
    client = FakeClient(robot_payload={"success": True, "code": 200, "data": None})

    with pytest.raises(ApiError, match="未查询到机器人"):
        run_info(args(name="ceshi1@corp"), make_runtime(client=client))


def test_not_found_api_error_adds_login_account_hint():
    client = FakeClient(
        robot_error=ApiError("参数错误， 未查询到机器人", code=400, request_id="req-2")
    )

    with pytest.raises(ApiError) as excinfo:
        run_info(args(name="ceshi1@corp"), make_runtime(client=client))

    assert "loginAccount" in (excinfo.value.hint or "")
    assert excinfo.value.request_id == "req-2"


def test_not_found_after_lookup_mentions_robot_account():
    client = FakeClient(
        accounts=[ACCOUNT],
        robot_error=ApiError("参数错误， 未查询到机器人", code=400),
    )

    with pytest.raises(ApiError) as excinfo:
        run_info(args(name="ceshi1"), make_runtime(client=client))

    assert "已用企业账号列表补全" in (excinfo.value.hint or "")
    assert client.calls[0]["path"] == ACCOUNT_LIST_PATH
    assert robot_calls(client)
