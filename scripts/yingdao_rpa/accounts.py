# -*- coding: utf-8 -*-
"""机器人账号名处理：企业版账号后缀的补全与校验。

影刀企业版的机器人账号形如 `ceshi1@csqy1`，`@` 及其后面的部分是
企业标识。用户只给 `ceshi1` 时，允许用配置里的 `enterpriseSuffix`
补全；既没有后缀也没有配置时，必须在本地拦截并提示。
"""

from __future__ import annotations

ACCOUNT_SUFFIX_HINT = (
    "请提供完整名称（如 ceshi1@csqy1），"
    "或在配置中设置 enterpriseSuffix（如 @csqy1），"
    "或本次使用 --suffix @csqy1。"
)


def normalize_suffix(value: str | None) -> str:
    """把企业后缀规范成 `@xxx`；空值返回空串。"""
    text = (value or "").strip()
    if not text:
        return ""
    if not text.startswith("@"):
        text = f"@{text}"
    if text == "@":
        raise ValueError("企业账号后缀不能只有 @")
    if "@" in text[1:]:
        raise ValueError("企业账号后缀只填 @ 后的企业标识，例如 @csqy1")
    return text


def resolve_account_name(name: str, suffix: str | None = "") -> str:
    """补全机器人账号名。

    - 名称已带 `@企业标识`：原样返回，不覆盖用户显式指定；
    - 名称不带后缀：用 suffix 补全；
    - 既没有后缀也没有配置：抛 ValueError，由命令层给出补充指引。
    """
    text = (name or "").strip()
    if not text:
        raise ValueError("机器人名称不能为空")

    if "@" in text:
        local, _, domain = text.partition("@")
        if not local.strip():
            raise ValueError("机器人名称 @ 前不能为空")
        if not domain.strip():
            raise ValueError("机器人名称 @ 后缺少企业标识，请补全或去掉多余的 @")
        return text

    normalized = normalize_suffix(suffix)
    if not normalized:
        raise ValueError("机器人名称缺少企业账号后缀")
    return f"{text}{normalized}"
