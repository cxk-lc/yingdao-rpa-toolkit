# -*- coding: utf-8 -*-
"""`robot` 子命令：查询单台机器人详情与状态（接口文档 4.2）。"""

from __future__ import annotations

import argparse
from typing import Any

from ..accounts import ACCOUNT_SUFFIX_HINT, resolve_account_name
from ..errors import ApiError, ParamError
from ..runtime import Runtime

ROBOT_QUERY_PATH = "/oapi/dispatch/v2/client/query"

ROBOT_STATUS_NAMES = {
    "connected": "已连接",
    "idle": "空闲",
    "allocated": "已分配",
    "running": "运行中",
    "offline": "离线",
}
ONLINE_STATUSES = frozenset({"connected", "idle", "allocated", "running"})
ROBOT_NOT_FOUND_HINT = (
    "确认机器人名称是否正确；若只填了账号前缀，请补充 enterpriseSuffix（如 @csqy1）"
    "或本次使用 --suffix；也可以改用 --uuid 查询。"
)


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("robot", help="机器人")
    actions = parser.add_subparsers(dest="robot_action", required=True, metavar="<动作>")

    info = actions.add_parser("info", parents=[common], help="按名称或 uuid 查询机器人状态")
    target = info.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--name",
        help="机器人账号名；缺少 @企业后缀 时按配置自动补全",
    )
    target.add_argument(
        "--uuid",
        help="机器人 uuid（不推荐：切换调度模式后会变化）",
    )
    info.add_argument(
        "--suffix",
        help="本次使用的企业账号后缀，如 @csqy1；优先于配置 enterpriseSuffix",
    )
    info.set_defaults(handler=run_info, command="robot info")


def _build_body(args: argparse.Namespace, runtime: Runtime) -> tuple[dict[str, Any], dict[str, Any]]:
    if args.uuid:
        if args.suffix is not None:
            raise ParamError("--suffix 只能与 --name 一起使用")
        robot_uuid = args.uuid.strip()
        if not robot_uuid:
            raise ParamError("--uuid 不能为空")
        return {"robotClientUuid": robot_uuid}, {"robotClientUuid": robot_uuid}

    suffix = args.suffix if args.suffix is not None else runtime.config.enterprise_suffix
    try:
        account_name = resolve_account_name(args.name, suffix)
    except ValueError as exc:
        raise ParamError(str(exc), hint=ACCOUNT_SUFFIX_HINT) from exc

    input_name = (args.name or "").strip()
    requested = {
        "inputName": input_name,
        "accountName": account_name,
        "suffixApplied": account_name != input_name,
    }
    return {"accountName": account_name}, requested


def _view(robot: dict[str, Any]) -> dict[str, Any]:
    view = dict(robot)
    status = str(view.get("status") or "")
    view["statusName"] = ROBOT_STATUS_NAMES.get(status, status)
    view["online"] = status in ONLINE_STATUSES if status else None
    view["idle"] = status == "idle" if status else None
    return view


def run_info(args: argparse.Namespace, runtime: Runtime) -> dict:
    body, requested = _build_body(args, runtime)

    if runtime.dry_run:
        return {
            "data": {
                "kind": "request_preview",
                "request": runtime.client.preview(
                    "POST", ROBOT_QUERY_PATH, body=body, show_secrets=runtime.show_secrets
                ),
                "requested": requested,
            },
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    try:
        payload = runtime.client.request("POST", ROBOT_QUERY_PATH, body=body)
    except ApiError as exc:
        if "未查询到机器人" in exc.message or "未找到" in exc.message:
            raise ApiError(
                exc.message,
                code=exc.code,
                request_id=exc.request_id,
                hint=ROBOT_NOT_FOUND_HINT,
            ) from exc
        raise

    robot = payload.get("data")
    if not isinstance(robot, dict) or not robot:
        raise ApiError(
            "未查询到机器人",
            request_id=payload.get("requestId"),
            hint=ROBOT_NOT_FOUND_HINT,
        )

    return {
        "data": {"kind": "robot", "requested": requested, "robot": _view(robot)},
        "meta": runtime.client.last_meta.to_dict(),
    }
