# -*- coding: utf-8 -*-
"""CLI 契约：stdout 永远是合法 JSON，退出码与异常类型一一对应。"""

from __future__ import annotations

import json
import time

import pytest

from yingdao_rpa.cli import main
from yingdao_rpa.client import TokenInfo
from yingdao_rpa.utils import parse_timestamp

ENV_KEYS = (
    "YD_BASE_URL",
    "YD_ACCESS_KEY_ID",
    "YD_ACCESS_KEY_SECRET",
    "YD_ACCESS_TOKEN",
    "YD_TIMEOUT",
    "YD_POLL_INTERVAL",
    "YD_MAX_POLL_SECONDS",
    "YD_DEFAULT_ACCOUNT_NAME",
    "YD_DEFAULT_ROBOT_GROUP_UUID",
)


@pytest.fixture
def cli_workspace(tmp_path, monkeypatch, isolated_user_config):
    monkeypatch.chdir(tmp_path)
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    return tmp_path


def run_json(capsys, argv):
    code = main(argv)
    captured = capsys.readouterr()
    return code, json.loads(captured.out), captured.err


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])

    assert excinfo.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


def test_config_show_outputs_single_json(cli_workspace, capsys):
    code, payload, _ = run_json(capsys, ["config", "show"])

    assert code == 0
    assert payload["schema_version"] == 1
    assert payload["ok"] is True
    assert payload["command"] == "config show"
    assert payload["data"]["base_url"] == "https://api.yingdao.com"
    assert payload["data"]["access_key_secret"] == ""


def test_auth_check_without_credentials_returns_2(cli_workspace, capsys):
    code, payload, stderr = run_json(capsys, ["auth", "check"])

    assert code == 2
    assert payload["ok"] is False
    assert payload["error"]["type"] == "ConfigError"
    assert "accessKeyId" in payload["error"]["message"]
    assert "提示" in stderr


def test_job_start_without_target_returns_2(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(capsys, ["job", "start", "--app-id", "app-1", "--dry-run"])

    assert code == 2
    assert payload["error"]["type"] == "ParamError"


def test_job_start_dry_run_never_sends_request(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(
        capsys,
        [
            "job",
            "start",
            "--app-id",
            "app-1",
            "--account-name",
            "robot@corp",
            "--param",
            "月份=2026-10",
            "--param",
            "页数=10:int",
            "--dry-run",
        ],
    )

    assert code == 0
    request = payload["data"]["request"]
    assert request["method"] == "POST"
    assert request["url"].endswith("/oapi/dispatch/v2/job/start")
    assert request["body"]["accountName"] == "robot@corp"
    assert request["body"]["params"][1] == {"name": "页数", "value": "10", "type": "int"}
    assert payload["meta"]["dry_run"] is True


def test_job_query_requires_job_uuid(cli_workspace, capsys):
    code, payload, _ = run_json(capsys, ["job", "query"])

    assert code == 2
    assert payload["ok"] is False
    assert payload["error"]["type"] == "ParamError"


def test_auth_check_dry_run_masks_credentials(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "9wncDaPR2gkErHd1@platform")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk-live-value")

    code, payload, _ = run_json(capsys, ["auth", "check", "--dry-run"])

    query = payload["data"]["request"]["query"]
    assert code == 0
    assert payload["meta"]["dry_run"] is True
    assert query["accessKeyId"] == "9wnc****form"
    assert query["accessKeySecret"] == "***"


def test_auth_check_dry_run_show_secrets_is_opt_in(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "9wncDaPR2gkErHd1@platform")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk-live-value")

    code, payload, _ = run_json(capsys, ["auth", "check", "--dry-run", "--show-secrets"])

    query = payload["data"]["request"]["query"]
    assert code == 0
    assert query["accessKeyId"] == "9wncDaPR2gkErHd1@platform"
    assert query["accessKeySecret"] == "sk-live-value"


def test_config_init_creates_template_and_refuses_second_run(cli_workspace, capsys):
    code, payload, _ = run_json(capsys, ["config", "init", "--scope", "project"])
    assert code == 0
    assert (cli_workspace / ".yingdao" / "config.json").is_file()

    code, payload, _ = run_json(capsys, ["config", "init", "--scope", "project"])
    assert code == 2
    assert payload["error"]["type"] == "ConfigError"


def test_text_format_stays_human_readable(cli_workspace, capsys):
    code = main(["config", "show", "--format", "text"])
    out = capsys.readouterr().out

    assert code == 0
    assert "base_url=https://api.yingdao.com" in out


class FakeTokenClient:
    def __init__(self, config, access_token="", **kwargs):
        self.config = config
        self.access_token = access_token

    def token_info(self):
        return TokenInfo(
            access_token="tok-full-123456",
            expires_in=7199,
            expires_at=time.time() + 7199,
            source="fetched",
        )


def test_auth_token_outputs_full_token_without_persisting(cli_workspace, capsys, monkeypatch):
    monkeypatch.setattr("yingdao_rpa.cli.YingDaoClient", FakeTokenClient)

    code, payload, _ = run_json(capsys, ["auth", "token"])

    assert code == 0
    assert payload["data"]["access_token"] == "tok-full-123456"
    assert payload["data"]["token_type"] == "Bearer"
    assert payload["data"]["persisted"] is False
    assert payload["data"]["source"] == "fetched"
    assert payload["data"]["expires_at"]


def test_auth_token_text_mode_prints_raw_token(cli_workspace, capsys, monkeypatch):
    monkeypatch.setattr("yingdao_rpa.cli.YingDaoClient", FakeTokenClient)

    code = main(["auth", "token", "--format", "text"])
    out = capsys.readouterr().out

    assert code == 0
    assert out.strip() == "tok-full-123456"


def test_auth_token_rejects_save(cli_workspace, capsys):
    code, payload, _ = run_json(capsys, ["auth", "token", "--save", "token.json"])

    assert code == 2
    assert "不落盘" in payload["error"]["message"]
    assert not (cli_workspace / "token.json").exists()


def test_access_token_flag_is_forwarded_to_client(cli_workspace, capsys, monkeypatch):
    captured = {}

    class CapturingClient(FakeTokenClient):
        def __init__(self, config, access_token="", **kwargs):
            super().__init__(config, access_token, **kwargs)
            captured["token"] = access_token

    monkeypatch.setattr("yingdao_rpa.cli.YingDaoClient", CapturingClient)
    monkeypatch.setenv("YD_ACCESS_TOKEN", "env-token")

    run_json(capsys, ["auth", "token", "--access-token", "flag-token"])

    assert captured["token"] == "flag-token"


def test_access_token_env_is_used_when_flag_absent(cli_workspace, capsys, monkeypatch):
    captured = {}

    class CapturingClient(FakeTokenClient):
        def __init__(self, config, access_token="", **kwargs):
            super().__init__(config, access_token, **kwargs)
            captured["token"] = access_token

    monkeypatch.setattr("yingdao_rpa.cli.YingDaoClient", CapturingClient)
    monkeypatch.setenv("YD_ACCESS_TOKEN", "env-token")

    run_json(capsys, ["auth", "token"])

    assert captured["token"] == "env-token"


def test_robot_info_without_suffix_previews_account_lookup(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(capsys, ["robot", "info", "--name", "ceshi1", "--dry-run"])

    assert code == 0
    data = payload["data"]
    assert data["resolution"] == "account-lookup"
    assert data["request"]["url"].endswith("/oapi/rpa/user/v1/list")
    assert data["request"]["query"]["accountKeyword"] == "ceshi1"
    assert data["followup"]["body"] == {"accountName": "<loginAccount>"}


def test_robot_info_dry_run_applies_suffix(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(
        capsys,
        ["robot", "info", "--name", "ceshi1", "--suffix", "@csqy1", "--dry-run"],
    )

    assert code == 0
    assert payload["data"]["request"]["body"] == {"accountName": "ceshi1@csqy1"}
    assert payload["data"]["requested"]["suffixApplied"] is True


def test_account_list_dry_run_builds_query(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(
        capsys,
        [
            "account",
            "list",
            "--keyword",
            "张三",
            "--account-type",
            "basic,senior",
            "--page",
            "2",
            "--size",
            "50",
            "--latest-login-begin",
            "2026-01-01",
            "--dry-run",
        ],
    )

    assert code == 0
    query = payload["data"]["request"]["query"]
    assert query["accountKeyword"] == "张三"
    assert query["accountTypes"] == ["basic", "senior"]
    assert query["page"] == 2
    assert query["size"] == 50
    assert query["latestLoginTimeBegin"] == parse_timestamp("2026-01-01")


@pytest.mark.parametrize(
    "extra",
    [
        ["--size", "200"],
        ["--page", "0"],
        ["--account-type", "vip"],
        ["--all", "--max-pages", "0"],
    ],
)
def test_account_list_rejects_invalid_arguments(cli_workspace, capsys, monkeypatch, extra):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(capsys, ["account", "list", "--dry-run", *extra])

    assert code == 2
    assert payload["error"]["type"] == "ParamError"


def test_app_list_dry_run_builds_body(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(
        capsys,
        ["app", "list", "--app-name", "测试", "--page", "2", "--size", "50", "--dry-run"],
    )

    assert code == 0
    body = payload["data"]["request"]["body"]
    assert body == {"page": "2", "size": "50", "appName": "测试"}


def test_app_runs_requires_app_or_time(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(capsys, ["app", "runs", "--dry-run"])

    assert code == 2
    assert payload["error"]["type"] == "ParamError"


def test_app_runs_dry_run_builds_body(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(
        capsys,
        ["app", "runs", "--app-id", "app-1", "--begin-date", "2026-01-01", "--dry-run"],
    )

    assert code == 0
    body = payload["data"]["request"]["body"]
    assert body["appId"] == "app-1"
    assert body["minId"] == 0
    assert body["beginDate"] == "2026-01-01 00:00:00"


def test_robot_tasks_dry_run_builds_body(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(
        capsys,
        [
            "robot",
            "tasks",
            "--app-id",
            "app-1",
            "--status",
            "error,finish",
            "--size",
            "50",
            "--dry-run",
        ],
    )

    assert code == 0
    body = payload["data"]["request"]["body"]
    assert body["robotUuid"] == "app-1"
    assert body["statusList"] == ["error", "finish"]
    assert body["size"] == 50
    assert body["cursorDirection"] == "next"


def test_robot_tasks_pre_direction_requires_cursor(cli_workspace, capsys, monkeypatch):
    monkeypatch.setenv("YD_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("YD_ACCESS_KEY_SECRET", "sk")

    code, payload, _ = run_json(
        capsys, ["robot", "tasks", "--direction", "pre", "--dry-run"]
    )

    assert code == 2
    assert payload["error"]["type"] == "ParamError"
