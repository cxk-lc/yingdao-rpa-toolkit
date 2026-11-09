# -*- coding: utf-8 -*-
"""命令层公共设施：全局参数与子命令注册约定。

每个命令模块约定实现：
    register(subparsers, common) -> None
    run(args, runtime) -> dict
"""

from __future__ import annotations

import argparse


def build_common() -> argparse.ArgumentParser:
    """所有叶子命令共享的全局参数。"""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="指定配置文件路径（默认向上查找 .yingdao/config.json）")
    common.add_argument("--base-url", help="API 域名，默认 https://api.yingdao.com")
    common.add_argument("--access-key-id", help="覆盖 YD_ACCESS_KEY_ID（不建议写在脚本里）")
    common.add_argument("--access-key-secret", help="覆盖 YD_ACCESS_KEY_SECRET（不建议写在脚本里）")
    common.add_argument(
        "--access-token",
        help="直接使用已有 accessToken（优先于凭据；也可用 YD_ACCESS_TOKEN 传入，token 不落盘）",
    )
    common.add_argument("--timeout", type=float, help="单次 HTTP 超时秒数，默认 30")
    common.add_argument("--format", choices=["json", "text"], default="json", help="输出格式，默认 json")
    common.add_argument(
        "--dry-run",
        action="store_true",
        help="只输出预览：不发请求、不写盘（config init 仅显示目标路径）",
    )
    common.add_argument(
        "--show-secrets",
        action="store_true",
        help="预览中输出密钥原文（默认掩码；仅在明确核对密钥时使用）",
    )
    common.add_argument("--save", help="把完整 JSON 结果另存到指定文件（auth token 禁用）")
    common.add_argument("--log-file", help="把 DEBUG 级日志追加写入指定文件")
    common.add_argument("--debug", action="store_true", help="在 stderr 输出调试日志")
    common.add_argument("--quiet", action="store_true", help="不输出 warnings")
    return common
