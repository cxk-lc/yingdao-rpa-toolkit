# -*- coding: utf-8 -*-
"""测试夹具：把 scripts/ 加入导入路径，并隔离用户级配置。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from yingdao_rpa.config import Config  # noqa: E402
from yingdao_rpa.transport import RawResponse  # noqa: E402


@pytest.fixture
def isolated_user_config(tmp_path, monkeypatch):
    """把用户级配置指向临时目录，避免读到开发机上的真实配置。"""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    target = home / ".yingdao" / "config.json"

    def fake_user_config_path() -> Path:
        return target

    monkeypatch.setattr("yingdao_rpa.config.user_config_path", fake_user_config_path)
    return target


@pytest.fixture
def fake_config() -> Config:
    return Config(
        base_url="https://example.test",
        access_key_id="test-ak-id",
        access_key_secret="test-ak-secret",
        timeout_seconds=5,
    )


def make_response(status: int, payload: dict, headers: dict[str, str] | None = None) -> RawResponse:
    return RawResponse(
        status=status,
        text=json.dumps(payload, ensure_ascii=False),
        headers=headers or {},
        elapsed_ms=1,
    )


@pytest.fixture
def response_factory():
    return make_response
