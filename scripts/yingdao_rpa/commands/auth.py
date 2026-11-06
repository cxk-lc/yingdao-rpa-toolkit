# -*- coding: utf-8 -*-
"""`auth` 子命令。

- `auth check`：验证凭据，确认能换到 token（只输出脱敏 token）。
- `auth token`：输出完整 accessToken，供其它命令直接传入；token 不落盘。
"""

from __future__ import annotations

import argparse
from datetime import datetime

from ..client import TOKEN_PATH
from ..errors import ParamError
from ..runtime import Runtime
from ..utils import mask_secret


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("auth", help="鉴权")
    actions = parser.add_subparsers(dest="auth_action", required=True, metavar="<动作>")

    check = actions.add_parser("check", parents=[common], help="验证凭据（输出脱敏 token）")
    check.set_defaults(handler=run_check, command="auth check")

    token = actions.add_parser("token", parents=[common], help="获取完整 accessToken，供其它命令传入")
    token.set_defaults(handler=run_token, command="auth token")


def _iso(expires_at: float) -> str | None:
    if not expires_at:
        return None
    return datetime.fromtimestamp(expires_at).astimezone().isoformat(timespec="seconds")


def run_check(args: argparse.Namespace, runtime: Runtime) -> dict:
    if runtime.dry_run:
        preview = runtime.client.preview(
            "GET",
            TOKEN_PATH,
            query={
                "accessKeyId": runtime.config.access_key_id,
                "accessKeySecret": runtime.config.access_key_secret,
            },
            need_token=False,
            show_secrets=runtime.show_secrets,
        )
        return {
            "data": {"kind": "request_preview", "request": preview},
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    info = runtime.client.create_token()
    return {
        "data": {
            "base_url": runtime.config.base_url,
            "expires_in": info.expires_in,
            "expires_at": _iso(info.expires_at),
            "source": info.source,
            "token_masked": mask_secret(info.access_token),
            "config_source": runtime.config.source,
        },
        "meta": {
            "base_url": runtime.config.base_url,
            "api_success": True,
            "dry_run": False,
        },
    }


def run_token(args: argparse.Namespace, runtime: Runtime) -> dict:
    if args.save:
        raise ParamError(
            "auth token 不允许 --save：accessToken 不落盘",
            hint="请把 stdout 中的 access_token 直接传给下一条命令的 --access-token，"
            "或写入进程环境变量 YD_ACCESS_TOKEN。",
        )

    if runtime.dry_run:
        preview = runtime.client.preview(
            "GET",
            TOKEN_PATH,
            query={
                "accessKeyId": runtime.config.access_key_id,
                "accessKeySecret": runtime.config.access_key_secret,
            },
            need_token=False,
            show_secrets=runtime.show_secrets,
        )
        return {
            "data": {"kind": "request_preview", "request": preview},
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    info = runtime.client.token_info()
    return {
        "data": {
            "access_token": info.access_token,
            "token_type": "Bearer",
            "expires_in": info.expires_in,
            "expires_at": _iso(info.expires_at),
            "source": info.source,
            "persisted": False,
            "base_url": runtime.config.base_url,
        },
        "meta": {
            "base_url": runtime.config.base_url,
            "api_success": info.source == "fetched",
            "dry_run": False,
        },
    }
