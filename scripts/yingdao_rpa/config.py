# -*- coding: utf-8 -*-
"""配置管理：命令行 > 环境变量 > 项目级 > 用户级。

项目级配置位于从当前目录向上最近的 `.yingdao/config.json`；
用户级配置位于 `~/.yingdao/config.json`。命令行参数优先级最高，
便于一次性的临时覆盖。密钥只从这些来源读取，不写回文件。
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .accounts import normalize_suffix
from .errors import CONFIG_HINT, ConfigError
from .utils import mask_secret

DEFAULT_BASE_URL = "https://api.yingdao.com"
CONFIG_DIRNAME = ".yingdao"
CONFIG_FILENAME = "config.json"
MAX_UPWARD_LEVELS = 8

CONFIG_TEMPLATE: dict[str, Any] = {
    "baseUrl": DEFAULT_BASE_URL,
    "accessKeyId": "<在此填写 accessKeyId>",
    "accessKeySecret": "<在此填写 accessKeySecret>",
    "timeoutSeconds": 30,
    "pollIntervalSeconds": 30,
    "maxPollSeconds": 1800,
    "defaultAccountName": "",
    "defaultRobotClientGroupUuid": "",
    "enterpriseSuffix": "",
}


@dataclass(frozen=True)
class Config:
    base_url: str = DEFAULT_BASE_URL
    access_key_id: str = ""
    access_key_secret: str = ""
    timeout_seconds: float = 30.0
    poll_interval_seconds: int = 30
    max_poll_seconds: int = 1800
    default_account_name: str = ""
    default_robot_client_group_uuid: str = ""
    enterprise_suffix: str = ""
    source: str = ""
    config_path: str = ""

    def __repr__(self) -> str:
        # 避免密钥随日志或异常堆栈泄漏
        return (
            f"Config(base_url={self.base_url!r}, access_key_id={mask_secret(self.access_key_id)!r}, "
            f"access_key_secret='***', source={self.source!r})"
        )

    def public_view(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "access_key_id": mask_secret(self.access_key_id),
            "access_key_secret": "***" if self.access_key_secret else "",
            "timeout_seconds": self.timeout_seconds,
            "poll_interval_seconds": self.poll_interval_seconds,
            "max_poll_seconds": self.max_poll_seconds,
            "default_account_name": self.default_account_name,
            "default_robot_client_group_uuid": self.default_robot_client_group_uuid,
            "enterprise_suffix": self.enterprise_suffix,
            "source": self.source,
            "config_path": self.config_path,
        }


def find_project_config(start: Path | None = None) -> Path | None:
    """从 start 向上逐级查找 `.yingdao/config.json`。"""
    current = (start or Path.cwd()).resolve()
    for _ in range(MAX_UPWARD_LEVELS):
        candidate = current / CONFIG_DIRNAME / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def user_config_path() -> Path:
    return Path.home() / CONFIG_DIRNAME / CONFIG_FILENAME


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"配置文件无法解析：{path}", hint=str(exc)) from exc
    if not isinstance(data, dict):
        raise ConfigError(f"配置文件顶层必须是 JSON 对象：{path}")
    return data


def _env_layer(env: Mapping[str, str]) -> dict[str, Any]:
    return {
        "baseUrl": env.get("YD_BASE_URL"),
        "accessKeyId": env.get("YD_ACCESS_KEY_ID"),
        "accessKeySecret": env.get("YD_ACCESS_KEY_SECRET"),
        "timeoutSeconds": env.get("YD_TIMEOUT"),
        "pollIntervalSeconds": env.get("YD_POLL_INTERVAL"),
        "maxPollSeconds": env.get("YD_MAX_POLL_SECONDS"),
        "defaultAccountName": env.get("YD_DEFAULT_ACCOUNT_NAME"),
        "defaultRobotClientGroupUuid": env.get("YD_DEFAULT_ROBOT_GROUP_UUID"),
        "enterpriseSuffix": env.get("YD_ENTERPRISE_SUFFIX"),
    }


def _cli_layer(args: Any) -> dict[str, Any]:
    if args is None:
        return {}
    return {
        "baseUrl": getattr(args, "base_url", None),
        "accessKeyId": getattr(args, "access_key_id", None),
        "accessKeySecret": getattr(args, "access_key_secret", None),
        "timeoutSeconds": getattr(args, "timeout", None),
        "defaultAccountName": getattr(args, "account_name", None),
    }


def _positive_float(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field_name} 必须是数字，当前为：{value!r}") from exc
    if number <= 0:
        raise ConfigError(f"{field_name} 必须大于 0，当前为：{value!r}")
    return number


def _positive_int(value: Any, field_name: str, minimum: int = 1) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field_name} 必须是整数，当前为：{value!r}") from exc
    if number < minimum:
        raise ConfigError(f"{field_name} 不能小于 {minimum}，当前为：{value!r}")
    return number


def load_config(
    args: Any = None,
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> Config:
    """按优先级合并四层配置并完成校验。"""
    env = os.environ if env is None else env
    explicit = getattr(args, "config", None) if args is not None else None

    if explicit:
        project_path: Path | None = Path(explicit).expanduser()
        if not project_path.is_file():
            raise ConfigError(f"指定的配置文件不存在：{project_path}")
        project_source = "explicit"
    else:
        project_path = find_project_config(cwd)
        project_source = "project"

    user_path = user_config_path()
    layers: list[tuple[str, dict[str, Any]]] = [
        ("cli", _cli_layer(args)),
        ("env", _env_layer(env)),
        (project_source, _read_json(project_path)),
        ("user", _read_json(user_path)),
    ]

    def pick(key: str, default: Any = None) -> tuple[Any, str | None]:
        for name, layer in layers:
            value = layer.get(key)
            if value is not None and value != "":
                return value, name
        return default, None

    base_url = str(pick("baseUrl", DEFAULT_BASE_URL)[0]).strip().rstrip("/")
    if not re.match(r"^https?://", base_url, re.IGNORECASE):
        raise ConfigError(
            f"baseUrl 必须以 http:// 或 https:// 开头，当前为：{base_url}",
            hint="公有云使用 https://api.yingdao.com；专有云填写专属域名。",
        )
    if "/oapi" in base_url.lower():
        raise ConfigError(
            f"baseUrl 只填域名，不要带接口路径：{base_url}",
            hint="例如 https://api.yingdao.com，而不是 https://api.yingdao.com/oapi。",
        )

    access_key_id, ak_source = pick("accessKeyId", "")
    access_key_secret, _ = pick("accessKeySecret", "")

    timeout = _positive_float(pick("timeoutSeconds", 30)[0], "timeoutSeconds")
    poll_interval = _positive_int(pick("pollIntervalSeconds", 30)[0], "pollIntervalSeconds", 5)
    max_poll = _positive_int(pick("maxPollSeconds", 1800)[0], "maxPollSeconds", 30)

    raw_suffix = str(pick("enterpriseSuffix", "")[0] or "").strip()
    try:
        enterprise_suffix = normalize_suffix(raw_suffix)
    except ValueError as exc:
        raise ConfigError(
            f"enterpriseSuffix 配置非法：{exc}",
            hint="只填企业标识或带 @ 的标识，例如 @csqy1（写 csqy1 会自动补 @）。",
        ) from exc

    config_path = ""
    if project_path is not None and project_path.is_file():
        config_path = str(project_path)
    elif user_path.is_file():
        config_path = str(user_path)

    return Config(
        base_url=base_url,
        access_key_id=str(access_key_id or "").strip(),
        access_key_secret=str(access_key_secret or "").strip(),
        timeout_seconds=timeout,
        poll_interval_seconds=poll_interval,
        max_poll_seconds=max_poll,
        default_account_name=str(pick("defaultAccountName", "")[0] or "").strip(),
        default_robot_client_group_uuid=str(
            pick("defaultRobotClientGroupUuid", "")[0] or ""
        ).strip(),
        enterprise_suffix=enterprise_suffix,
        source=ak_source or "",
        config_path=config_path,
    )


def require_credentials(config: Config) -> None:
    if not config.access_key_id or not config.access_key_secret:
        raise ConfigError("缺少 accessKeyId / accessKeySecret", hint=CONFIG_HINT)
    for name, value in (
        ("accessKeyId", config.access_key_id),
        ("accessKeySecret", config.access_key_secret),
    ):
        if value.startswith("<") and value.endswith(">"):
            raise ConfigError(
                f"{name} 仍是配置模板里的占位符：{value}",
                hint=f"打开 {config.config_path or '配置文件'} 填入真实密钥；或在控制台重新创建密钥对。",
            )


def write_config_template(
    scope: str | None = None,
    *,
    cwd: Path | None = None,
    force: bool = False,
) -> tuple[Path, str]:
    """生成配置模板，返回 (路径, 作用域)。已有文件默认拒绝覆盖。"""
    if scope not in (None, "project", "user"):
        raise ConfigError(f"未知的 scope：{scope}", hint="可选值为 project 或 user。")

    cwd = cwd or Path.cwd()
    if scope is None:
        scope = "project" if (cwd / ".git").exists() else "user"

    target = cwd / CONFIG_DIRNAME / CONFIG_FILENAME if scope == "project" else user_config_path()
    if target.exists() and not force:
        raise ConfigError(
            f"配置文件已存在，未覆盖：{target}",
            hint="如需重新生成，先备份并删除该文件，或显式加 --force。",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(CONFIG_TEMPLATE, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target, scope
