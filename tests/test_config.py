# -*- coding: utf-8 -*-
"""配置优先级、校验与脱敏。"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from yingdao_rpa.config import (
    Config,
    find_project_config,
    load_config,
    require_credentials,
    resolve_config_target,
    write_config_template,
)
from yingdao_rpa.errors import ConfigError


def write(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_project_config_is_used_when_no_env_or_cli(tmp_path, isolated_user_config):
    write(
        tmp_path / ".yingdao" / "config.json",
        {"baseUrl": "https://api.example.com", "accessKeyId": "from-project"},
    )

    config = load_config(None, env={}, cwd=tmp_path)

    assert config.base_url == "https://api.example.com"
    assert config.access_key_id == "from-project"
    assert config.source == "project"
    assert config.config_path.endswith("config.json")


def test_env_overrides_project_and_cli_overrides_env(tmp_path, isolated_user_config):
    write(tmp_path / ".yingdao" / "config.json", {"accessKeyId": "project"})

    env_config = load_config(None, env={"YD_ACCESS_KEY_ID": "env"}, cwd=tmp_path)
    assert env_config.access_key_id == "env"
    assert env_config.source == "env"

    args = SimpleNamespace(access_key_id="cli")
    cli_config = load_config(args, env={"YD_ACCESS_KEY_ID": "env"}, cwd=tmp_path)
    assert cli_config.access_key_id == "cli"
    assert cli_config.source == "cli"


def test_user_config_is_last_resort(tmp_path, isolated_user_config):
    write(isolated_user_config, {"accessKeyId": "from-user", "baseUrl": "https://user.example.com"})

    config = load_config(None, env={}, cwd=tmp_path)

    assert config.access_key_id == "from-user"
    assert config.source == "user"


def test_project_search_does_not_treat_user_config_as_project(tmp_path, isolated_user_config):
    write(isolated_user_config, {"accessKeyId": "from-user"})

    assert find_project_config(tmp_path) is None


def test_base_url_validation_rejects_path(tmp_path, isolated_user_config):
    write(tmp_path / ".yingdao" / "config.json", {"baseUrl": "https://api.yingdao.com/oapi"})

    with pytest.raises(ConfigError, match="不要带接口路径"):
        load_config(None, env={}, cwd=tmp_path)


def test_base_url_requires_scheme(tmp_path, isolated_user_config):
    with pytest.raises(ConfigError, match="http"):
        load_config(None, env={"YD_BASE_URL": "api.yingdao.com"}, cwd=tmp_path)


def test_timeout_must_be_positive(tmp_path, isolated_user_config):
    with pytest.raises(ConfigError, match="timeoutSeconds"):
        load_config(None, env={"YD_TIMEOUT": "0"}, cwd=tmp_path)


def test_explicit_config_must_exist(tmp_path, isolated_user_config):
    args = SimpleNamespace(config=str(tmp_path / "missing.json"))

    with pytest.raises(ConfigError, match="不存在"):
        load_config(args, env={}, cwd=tmp_path)


def test_public_view_masks_secrets():
    config = Config(
        access_key_id="EBCgDuVc1m5kPfjt@platform",
        access_key_secret="CkDqYb4e1NRr7HM2",
    )

    view = config.public_view()

    assert "CkDqYb4e1NRr7HM2" not in json.dumps(view, ensure_ascii=False)
    assert view["access_key_secret"] == "***"
    assert view["access_key_id"].startswith("EBCg")
    assert "****" in view["access_key_id"]


def test_repr_never_exposes_secret():
    config = Config(access_key_id="abcdefgh1234", access_key_secret="super-secret-value")

    assert "super-secret-value" not in repr(config)


def test_enterprise_suffix_is_normalized(tmp_path, isolated_user_config):
    write(tmp_path / ".yingdao" / "config.json", {"enterpriseSuffix": "csqy1"})

    config = load_config(None, env={}, cwd=tmp_path)

    assert config.enterprise_suffix == "@csqy1"
    assert config.public_view()["enterprise_suffix"] == "@csqy1"


def test_invalid_enterprise_suffix_is_rejected(tmp_path, isolated_user_config):
    write(tmp_path / ".yingdao" / "config.json", {"enterpriseSuffix": "@"})

    with pytest.raises(ConfigError, match="enterpriseSuffix"):
        load_config(None, env={}, cwd=tmp_path)


def test_placeholder_credentials_are_rejected():
    config = Config(
        access_key_id="<在此填写 accessKeyId>",
        access_key_secret="<在此填写 accessKeySecret>",
    )

    with pytest.raises(ConfigError, match="占位符"):
        require_credentials(config)


def test_write_config_template_refuses_overwrite(tmp_path):
    path, scope = write_config_template("project", cwd=tmp_path)

    assert scope == "project"
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8"))["baseUrl"]

    with pytest.raises(ConfigError, match="已存在"):
        write_config_template("project", cwd=tmp_path)


def test_write_config_template_force_overwrites(tmp_path):
    path, _ = write_config_template("project", cwd=tmp_path)
    path.write_text("{}", encoding="utf-8")

    write_config_template("project", cwd=tmp_path, force=True)

    assert "accessKeyId" in path.read_text(encoding="utf-8")


def test_resolve_config_target_does_not_create_file(tmp_path):
    target, scope = resolve_config_target("project", cwd=tmp_path)

    assert scope == "project"
    assert target == tmp_path / ".yingdao" / "config.json"
    assert not target.exists()


def test_resolve_config_target_defaults_to_project_when_git_exists(tmp_path):
    (tmp_path / ".git").mkdir()

    target, scope = resolve_config_target(cwd=tmp_path)

    assert scope == "project"
    assert target == tmp_path / ".yingdao" / "config.json"
    assert not target.exists()
