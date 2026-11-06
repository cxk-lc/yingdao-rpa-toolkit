# -*- coding: utf-8 -*-
"""`auth` 子命令：验证凭据并展示 token 有效期（不输出完整 token）。"""

from __future__ import annotations

import argparse
from datetime import datetime

from ..client import TOKEN_PATH
from ..runtime import Runtime
from ..utils import mask_secret


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("auth", help="鉴权")
    actions = parser.add_subparsers(dest="auth_action", required=True, metavar="<动作>")

    check = actions.add_parser("check", parents=[common], help="验证凭据并获取 accessToken")
    check.add_argument("--refresh", action="store_true", help="忽略本地缓存，强制重新获取")
    check.set_defaults(handler=run_check, command="auth check")


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
        )
        return {
            "data": {"kind": "request_preview", "request": preview},
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    info = runtime.client.create_token(force=args.refresh)
    expires_at = datetime.fromtimestamp(info.expires_at).astimezone().isoformat(timespec="seconds")
    return {
        "data": {
            "base_url": runtime.config.base_url,
            "expires_in": info.expires_in,
            "expires_at": expires_at,
            "cached": info.cached,
            "token_masked": mask_secret(info.access_token),
            "config_source": runtime.config.source,
        },
        "meta": {
            "base_url": runtime.config.base_url,
            "api_success": True,
            "token_cached": info.cached,
            "dry_run": False,
        },
    }
