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


# 预览默认掩码：命中这些词根的字段整体隐藏，accessKeyId 这类标识保留首尾各 4 位
FULL_MASK_WORDS = ("secret", "password", "token", "credential")
PARTIAL_MASK_WORDS = ("accesskeyid", "accesskey", "appkey")


def _mask_field(key: str, value: Any) -> Any:
    lowered = str(key).lower()
    if any(word in lowered for word in FULL_MASK_WORDS):
        return "***" if value else ""
    if any(word in lowered for word in PARTIAL_MASK_WORDS):
        return mask_secret(str(value)) if value else ""
    return sanitize_for_preview(value)


def sanitize_for_preview(value: Any, *, show_secrets: bool = False) -> Any:
    """递归掩码预览内容：默认隐藏密钥，只有显式要求原文时才原样返回。

    - `secret` / `token` 一类字段整体显示为 `***`；
    - `accessKeyId` 一类标识保留首尾各 4 位，便于核对是哪把密钥。
    """
    if show_secrets:
        return value
    if isinstance(value, dict):
        return {key: _mask_field(key, item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_for_preview(item) for item in value]
    return value


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
