# -*- coding: utf-8 -*-
"""CLI 契约：stdout 永远是合法 JSON，退出码与异常类型一一对应。"""

from __future__ import annotations

import json

import pytest

from yingdao_rpa.cli import main

ENV_KEYS = (
    "YD_BASE_URL",
    "YD_ACCESS_KEY_ID",
    "YD_ACCESS_KEY_SECRET",
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
