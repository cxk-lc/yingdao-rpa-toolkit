# -*- coding: utf-8 -*-
"""CLI 装配层：解析参数 → 组装配置与客户端 → 执行命令 → 统一输出。

这一层只做编排与兜底：任何异常都必须收敛成一条 JSON + 固定退出码，
保证调用方（人或 AI）拿到的永远是可解析的结果。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from typing import Any, Sequence

from . import __version__
from .client import YingDaoClient
from .commands import register_all
from .commands.common import build_common
from .config import load_config
from .errors import ApiError, NetworkError, ParamError, ToolError
from .logging_setup import get_logger, setup_logging
from .output import emit, make_error, make_success, now_iso
from .runtime import Runtime

logger = get_logger("cli")


class JsonArgumentParser(argparse.ArgumentParser):
    """参数错误也走统一 JSON 输出，而不是 argparse 默认的纯文本退出。"""

    def error(self, message: str) -> None:  # type: ignore[override]
        raise ParamError(
            message,
            hint="运行 `python scripts/yd.py <命令> --help` 查看可用参数。",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        prog="yd.py",
        description="影刀 RPA 开放 API 命令行工具（Skill + Python CLI）",
    )
    parser.add_argument("--version", action="version", version=f"yingdao-rpa-toolkit {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<命令>")
    register_all(subparsers, build_common())
    return parser


def _guess_command(argv: Sequence[str], args: argparse.Namespace | None) -> str:
    if args is not None and getattr(args, "command", None):
        return str(args.command)
    tokens = [token for token in argv if not token.startswith("-")]
    return " ".join(tokens[:2]) if tokens else ""


def main(argv: list[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()

    started_at = now_iso()
    started = time.monotonic()
    args: argparse.Namespace | None = None

    try:
        args = parser.parse_args(argv_list)
        if args.command == "auth token" and args.save:
            # 在发请求前拦截，且后续错误输出也不落盘
            raise ParamError(
                "auth token 不允许 --save：accessToken 不落盘",
                hint="请把 stdout 中的 access_token 直接传给下一条命令的 --access-token，"
                "或写入进程环境变量 YD_ACCESS_TOKEN。",
            )
        setup_logging(
            level="debug" if args.debug else "warning",
            log_file=args.log_file,
        )
        config = load_config(args)
        access_token = (args.access_token or os.environ.get("YD_ACCESS_TOKEN", "")).strip()
        if access_token:
            logger.debug("使用调用方传入的 accessToken（仅内存，不落盘）")
        client = YingDaoClient(config, access_token=access_token)
        runtime = Runtime(config=config, client=client, dry_run=args.dry_run, quiet=args.quiet)
        logger.debug("生效配置：%r", config)

        result: dict[str, Any] = args.handler(args, runtime) or {}
        exit_code = int(result.get("exit_code", 0))
        payload = make_success(
            command=str(args.command),
            data=result.get("data"),
            warnings=[] if args.quiet else list(result.get("warnings") or []),
            meta=result.get("meta") or client.last_meta.to_dict(),
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
    except ToolError as exc:
        exit_code = exc.exit_code
        payload = make_error(
            command=_guess_command(argv_list, args),
            error=exc,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
        print(f"✗ [{exc.kind}] {exc.message}", file=sys.stderr)
        if exc.hint:
            print(f"  提示：{exc.hint}", file=sys.stderr)
    except KeyboardInterrupt:
        error = NetworkError("操作已被用户中断", hint="可重新执行同一命令。")
        exit_code = error.exit_code
        payload = make_error(
            command=_guess_command(argv_list, args),
            error=error,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
        print(f"✗ [{error.kind}] {error.message}", file=sys.stderr)
    except Exception as exc:  # 兜底：保证 stdout 仍是可解析的 JSON
        error = ApiError(
            f"未预期错误：{type(exc).__name__}: {exc}",
            hint="加 --debug 查看堆栈；若持续出现请保留完整命令与输出。",
        )
        exit_code = error.exit_code
        payload = make_error(
            command=_guess_command(argv_list, args),
            error=error,
            started_at=started_at,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
        print(f"✗ [{error.kind}] {error.message}", file=sys.stderr)
        if args is not None and getattr(args, "debug", False):
            traceback.print_exc()

    fmt = getattr(args, "format", "json") if args is not None else "json"
    save_path = getattr(args, "save", None) if args is not None else None
    if getattr(args, "command", "") == "auth token":
        save_path = None
    try:
        emit(payload, fmt=fmt, save_path=save_path)
    except OSError as exc:
        print(f"✗ 结果写出失败：{exc}", file=sys.stderr)
        return 1
    return exit_code
