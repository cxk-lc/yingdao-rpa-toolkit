# -*- coding: utf-8 -*-
"""`config` 子命令：生成配置模板、查看生效配置。"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..config import write_config_template
from ..runtime import Runtime


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("config", help="配置管理")
    actions = parser.add_subparsers(dest="config_action", required=True, metavar="<动作>")

    init = actions.add_parser("init", parents=[common], help="生成配置模板")
    init.add_argument("--scope", choices=["project", "user"], help="模板位置，默认项目级（有 .git 时）")
    init.add_argument("--force", action="store_true", help="覆盖已存在的配置文件")
    init.set_defaults(handler=run_init, command="config init")

    show = actions.add_parser("show", parents=[common], help="查看生效配置（密钥脱敏）")
    show.set_defaults(handler=run_show, command="config show")


def run_init(args: argparse.Namespace, runtime: Runtime) -> dict:
    path, scope = write_config_template(args.scope, cwd=Path.cwd(), force=args.force)
    return {
        "data": {"path": str(path), "scope": scope, "config_file": str(path)},
        "meta": {"base_url": runtime.config.base_url, "dry_run": runtime.dry_run},
    }


def run_show(args: argparse.Namespace, runtime: Runtime) -> dict:
    return {
        "data": runtime.config.public_view(),
        "meta": {"base_url": runtime.config.base_url, "dry_run": runtime.dry_run},
    }
