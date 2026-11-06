# -*- coding: utf-8 -*-
"""通用小工具：脱敏与时间格式化。"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def mask_secret(value: str | None, keep: int = 4) -> str:
    """把密钥/令牌变成 `abcd****wxyz`，长度不足时整体隐藏。"""
    if not value:
        return ""
    if len(value) <= keep * 2:
        return "****"
    return f"{value[:keep]}****{value[-keep:]}"


def now_iso() -> str:
    """本地时区的 ISO 时间，精确到秒。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """按 key 名脱敏字典中的敏感字段，用于日志与调试输出。"""
    sensitive = ("secret", "token", "password", "accesskey")
    result: dict[str, Any] = {}
    for key, value in data.items():
        if any(word in key.lower() for word in sensitive):
            result[key] = "***" if value else ""
        else:
            result[key] = value
    return result
