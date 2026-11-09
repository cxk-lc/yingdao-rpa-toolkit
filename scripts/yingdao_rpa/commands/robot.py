# -*- coding: utf-8 -*-
"""`robot` 子命令：查询单台机器人详情与状态（接口文档 4.2）。

名称解析顺序：
1. 已带 `@企业标识`：原样使用；
2. 显式 `--suffix`：按指定后缀补全；
3. 只有前缀：先用 `account list` 找到对应账号的 `loginAccount`；
4. 查不到账号：回退到配置 `enterpriseSuffix`；
5. 都没有：本地拦截并提示补充。
"""

from __future__ import annotations

import argparse
from typing import Any

from ..accounts import ACCOUNT_SUFFIX_HINT, resolve_account_name
from ..errors import ApiError, ParamError, ToolError
from ..logging_setup import get_logger
from ..runtime import Runtime
from ..utils import parse_datetime_text
from .account import ACCOUNT_LIST_PATH, LOOKUP_PAGE_SIZE, match_accounts, query_accounts
from .job import APP_STATUS_CODES, APP_STATUS_NAMES

ROBOT_QUERY_PATH = "/oapi/dispatch/v2/client/query"
TASK_LIST_PATH = "/oapi/dispatch/v2/job/list"

DEFAULT_TASK_SIZE = 20
MAX_TASK_SIZE = 100
DEFAULT_TASK_MAX_PAGES = 50
TASK_DIRECTIONS = ("next", "pre")

ROBOT_STATUS_NAMES = {
    "connected": "已连接",
    "idle": "空闲",
    "allocated": "已分配",
    "running": "运行中",
    "offline": "离线",
}
ONLINE_STATUSES = frozenset({"connected", "idle", "allocated", "running"})
ROBOT_NOT_FOUND_HINT = (
    "确认机器人名称是否正确；若只给了账号前缀，工具会先用企业账号列表补全 loginAccount。"
    "也可以直接传完整 loginAccount（含 @企业标识），或改用 --uuid 查询。"
)
ROBOT_NOT_FOUND_AFTER_LOOKUP_HINT = (
    "已用企业账号列表补全 loginAccount，但未查到机器人；"
    "请确认该账号是否已作为机器人接入调度，或直接传完整机器人名称 / 改用 --uuid。"
)
LOOKUP_FAILED_HINT = "也可以直接传入完整 loginAccount（含 @企业标识）来跳过企业账号查询。"

logger = get_logger("robot")


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("robot", help="机器人")
    actions = parser.add_subparsers(dest="robot_action", required=True, metavar="<动作>")

    info = actions.add_parser("info", parents=[common], help="按名称或 uuid 查询机器人状态")
    target = info.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--name",
        help="机器人账号名；缺少 @企业标识 时先查企业账号再补全",
    )
    target.add_argument(
        "--uuid",
        help="机器人 uuid（不推荐：切换调度模式后会变化）",
    )
    info.add_argument(
        "--suffix",
        help="本次使用的企业账号后缀，如 @csqy1；显式指定后跳过企业账号查询",
    )
    info.set_defaults(handler=run_info, command="robot info")

    tasks = actions.add_parser("tasks", parents=[common], help="查询机器人任务队列与历史记录")
    tasks.add_argument("--app-id", "--robot-uuid", dest="app_id", help="应用 uuid（接口字段 robotUuid）")
    tasks.add_argument("--robot-client-uuid", help="机器人 uuid")
    tasks.add_argument("--schedule-uuid", help="计划 uuid")
    tasks.add_argument(
        "--status",
        action="append",
        metavar="CODE",
        help="运行状态，可重复或逗号分隔：" + " / ".join(APP_STATUS_CODES),
    )
    tasks.add_argument("--trigger-begin", help="触发时间起点，YYYY-MM-DD [HH:MM:SS]")
    tasks.add_argument("--trigger-end", help="触发时间终点，YYYY-MM-DD [HH:MM:SS]")
    tasks.add_argument("--cursor-id", type=int, help="游标 id；第一页不传")
    tasks.add_argument("--direction", choices=TASK_DIRECTIONS, help="翻页方向，默认 next")
    tasks.add_argument(
        "--size", type=int, help=f"每页条数，默认 {DEFAULT_TASK_SIZE}，最大 {MAX_TASK_SIZE}"
    )
    tasks.add_argument("--all", action="store_true", help="沿当前方向自动翻页")
    tasks.add_argument(
        "--max-pages", type=int, help=f"--all 时最多拉取页数，默认 {DEFAULT_TASK_MAX_PAGES}"
    )
    tasks.add_argument("--query-api", action="store_true", help="查询控制台 API 执行记录列表")
    tasks.set_defaults(handler=run_tasks, command="robot tasks")


def _requested(
    input_name: str,
    account_name: str | None,
    resolved_by: str,
    *,
    suffix_applied: bool = False,
    lookup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "inputName": input_name,
        "accountName": account_name,
        "resolvedBy": resolved_by,
        "suffixApplied": suffix_applied,
    }
    if lookup:
        data["lookup"] = lookup
    return data


def _requested_by_uuid(robot_uuid: str) -> dict[str, Any]:
    """`--uuid` 模式的解析记录：与名称模式保持一致的字段形状。"""
    return {
        "inputName": None,
        "accountName": None,
        "resolvedBy": "uuid",
        "suffixApplied": False,
        "robotClientUuid": robot_uuid,
    }


def _resolve_with_suffix(
    name: str,
    suffix: str,
    *,
    lookup: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    try:
        account_name = resolve_account_name(name, suffix)
    except ValueError as exc:
        raise ParamError(str(exc), hint=ACCOUNT_SUFFIX_HINT) from exc
    return account_name, _requested(
        name,
        account_name,
        "suffix",
        suffix_applied=account_name != name,
        lookup=lookup,
    )


def _lookup_account(name: str, runtime: Runtime) -> tuple[str, dict[str, Any]]:
    """用企业账号列表把前缀补成 loginAccount；失败时回退到配置后缀。"""
    suffix = runtime.config.enterprise_suffix
    try:
        accounts = query_accounts(runtime.client, name)
        matches = match_accounts(accounts, name)
    except ToolError as exc:
        if suffix:
            logger.warning("企业账号查询失败，回退到配置后缀：%s", exc.message)
            account_name, requested = _resolve_with_suffix(
                name,
                suffix,
                lookup={"keyword": name, "matched": 0, "fallback": "account-query-failed"},
            )
            requested["fallback"] = "account-query-failed"
            return account_name, requested
        if not exc.hint:
            exc.hint = LOOKUP_FAILED_HINT
        raise

    if len(matches) == 1:
        login_account = str(matches[0].get("loginAccount") or "").strip()
        if login_account:
            return login_account, _requested(
                name,
                login_account,
                "account",
                lookup={"keyword": name, "matched": 1},
            )

    if len(matches) > 1:
        candidates = [
            str(account.get("loginAccount") or "").strip()
            for account in matches
            if account.get("loginAccount")
        ]
        if candidates:
            preview = "、".join(candidates[:5])
            if len(candidates) > 5:
                preview += " 等"
            raise ParamError(
                f"机器人名称匹配到 {len(candidates)} 个企业账号，无法确定用哪个",
                hint=f"请改用完整 loginAccount：{preview}",
            )

    if suffix:
        account_name, requested = _resolve_with_suffix(
            name,
            suffix,
            lookup={"keyword": name, "matched": 0},
        )
        requested["fallback"] = "no-account-match"
        return account_name, requested

    raise ParamError(
        "未找到匹配的企业账号，且没有可用的企业账号后缀",
        hint=ACCOUNT_SUFFIX_HINT,
    )


def _view(robot: dict[str, Any]) -> dict[str, Any]:
    view = dict(robot)
    status = str(view.get("status") or "")
    view["statusName"] = ROBOT_STATUS_NAMES.get(status, status)
    view["online"] = status in ONLINE_STATUSES if status else None
    view["idle"] = status == "idle" if status else None
    return view


def _execute(body: dict[str, Any], requested: dict[str, Any], runtime: Runtime) -> dict:
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
            hint = (
                ROBOT_NOT_FOUND_AFTER_LOOKUP_HINT
                if requested.get("resolvedBy") == "account"
                else ROBOT_NOT_FOUND_HINT
            )
            raise ApiError(
                exc.message,
                code=exc.code,
                request_id=exc.request_id,
                hint=hint,
            ) from exc
        raise

    robot = payload.get("data")
    if not isinstance(robot, dict) or not robot:
        raise ApiError(
            "未查询到机器人",
            request_id=payload.get("requestId"),
            hint=(
                ROBOT_NOT_FOUND_AFTER_LOOKUP_HINT
                if requested.get("resolvedBy") == "account"
                else ROBOT_NOT_FOUND_HINT
            ),
        )

    return {
        "data": {"kind": "robot", "requested": requested, "robot": _view(robot)},
        "meta": runtime.client.last_meta.to_dict(),
    }


def _dry_run_lookup(name: str, runtime: Runtime) -> dict:
    data: dict[str, Any] = {
        "kind": "request_preview",
        "resolution": "account-lookup",
        "request": runtime.client.preview(
            "GET",
            ACCOUNT_LIST_PATH,
            query={"accountKeyword": name, "page": 1, "size": LOOKUP_PAGE_SIZE},
            show_secrets=runtime.show_secrets,
        ),
        "followup": {
            "method": "POST",
            "url": runtime.config.base_url + ROBOT_QUERY_PATH,
            "body": {"accountName": "<loginAccount>"},
        },
        "requested": _requested(name, None, "account-lookup"),
    }
    suffix = runtime.config.enterprise_suffix
    if suffix:
        data["fallback"] = {
            "accountName": f"{name}{suffix}",
            "reason": "企业账号无匹配时使用配置后缀",
        }
    return {
        "data": data,
        "meta": {"base_url": runtime.config.base_url, "dry_run": True},
    }


def run_info(args: argparse.Namespace, runtime: Runtime) -> dict:
    if args.uuid:
        if args.suffix is not None:
            raise ParamError("--suffix 只能与 --name 一起使用")
        robot_uuid = (args.uuid or "").strip()
        if not robot_uuid:
            raise ParamError("--uuid 不能为空")
        return _execute(
            {"robotClientUuid": robot_uuid},
            _requested_by_uuid(robot_uuid),
            runtime,
        )

    name = (args.name or "").strip()
    if not name:
        raise ParamError("机器人名称不能为空")

    if "@" in name:
        return _execute(
            {"accountName": name},
            _requested(name, name, "input"),
            runtime,
        )

    if args.suffix is not None:
        account_name, requested = _resolve_with_suffix(name, args.suffix)
        return _execute({"accountName": account_name}, requested, runtime)

    if runtime.dry_run:
        return _dry_run_lookup(name, runtime)

    account_name, requested = _lookup_account(name, runtime)
    return _execute({"accountName": account_name}, requested, runtime)


def _parse_task_statuses(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for raw in values or []:
        for item in str(raw).split(","):
            code = item.strip().lower()
            if not code:
                continue
            if code not in APP_STATUS_CODES:
                raise ParamError(
                    f"未知运行状态：{item}",
                    hint="可选值：" + " / ".join(APP_STATUS_CODES),
                )
            if code not in result:
                result.append(code)
    return result


def _task_time(value: str | None, field: str) -> str | None:
    try:
        return parse_datetime_text(value, field=field)
    except ValueError as exc:
        raise ParamError(str(exc)) from exc


def _max_pages(value: int | None) -> int:
    pages = value if value is not None else DEFAULT_TASK_MAX_PAGES
    if pages < 1:
        raise ParamError(f"--max-pages 必须大于等于 1，当前为：{pages}")
    return pages


def build_tasks_body(args: argparse.Namespace) -> tuple[dict[str, Any], int, str]:
    size = args.size if args.size is not None else DEFAULT_TASK_SIZE
    if not (1 <= size <= MAX_TASK_SIZE):
        raise ParamError(f"--size 必须在 1~{MAX_TASK_SIZE} 之间，当前为：{size}")

    direction = args.direction or "next"
    if direction == "pre" and args.cursor_id is None:
        raise ParamError("--direction pre 必须同时提供 --cursor-id")

    body: dict[str, Any] = {"cursorDirection": direction, "size": size}
    if args.app_id and args.app_id.strip():
        body["robotUuid"] = args.app_id.strip()
    if args.robot_client_uuid and args.robot_client_uuid.strip():
        body["robotClientUuid"] = args.robot_client_uuid.strip()
    if args.schedule_uuid and args.schedule_uuid.strip():
        body["scheduleUuid"] = args.schedule_uuid.strip()

    statuses = _parse_task_statuses(args.status)
    if statuses:
        body["statusList"] = statuses

    begin = _task_time(args.trigger_begin, "触发时间起点")
    end = _task_time(args.trigger_end, "触发时间终点")
    if begin and end and begin > end:
        raise ParamError("触发时间起点不能晚于终点")
    if begin:
        body["triggerTimeBegin"] = begin
    if end:
        body["triggerTimeEnd"] = end

    if args.cursor_id is not None:
        body["cursorId"] = args.cursor_id
    if args.query_api:
        body["queryApi"] = True
    return body, size, direction


def _task_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def _task_cursor(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "hasData": data.get("hasData"),
        "nextId": data.get("nextId"),
        "preId": data.get("preId"),
        "cursorDirection": data.get("cursorDirection"),
    }


def _task_view(row: dict[str, Any]) -> dict[str, Any]:
    view = dict(row)
    status = str(view.get("status") or "")
    view["statusName"] = APP_STATUS_NAMES.get(status, status)
    return view


def _task_result(
    items: list[dict[str, Any]],
    cursor: dict[str, Any],
    body: dict[str, Any],
    *,
    requested: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "robot_task_list",
        "items": items,
        "count": len(items),
        "cursor": cursor,
        "filters": {
            key: value
            for key, value in body.items()
            if key not in ("cursorId", "cursorDirection", "size")
        },
        "requested": requested,
    }


def run_tasks(args: argparse.Namespace, runtime: Runtime) -> dict:
    body, size, direction = build_tasks_body(args)
    max_pages = _max_pages(args.max_pages)

    if runtime.dry_run:
        return {
            "data": {
                "kind": "request_preview",
                "request": runtime.client.preview(
                    "POST", TASK_LIST_PATH, body=body, show_secrets=runtime.show_secrets
                ),
                "requested": {
                    "all": args.all,
                    "maxPages": max_pages if args.all else None,
                },
            },
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    if not args.all:
        payload = runtime.client.request("POST", TASK_LIST_PATH, body=body)
        data = _task_data(payload)
        rows = data.get("dataList") if isinstance(data.get("dataList"), list) else []
        items = [_task_view(row) for row in rows if isinstance(row, dict)]
        return {
            "data": _task_result(
                items,
                _task_cursor(data),
                body,
                requested={
                    "all": False,
                    "cursorId": args.cursor_id,
                    "direction": direction,
                    "size": size,
                },
            ),
            "meta": runtime.client.last_meta.to_dict(),
        }

    items: list[dict[str, Any]] = []
    cursor: dict[str, Any] = {}
    warnings: list[str] = []
    seen: set[str] = set()
    current = args.cursor_id
    fetched_pages = 0

    while True:
        page_body = dict(body)
        if current is not None:
            page_body["cursorId"] = current
        payload = runtime.client.request("POST", TASK_LIST_PATH, body=page_body)
        data = _task_data(payload)
        rows = data.get("dataList") if isinstance(data.get("dataList"), list) else []
        cursor = _task_cursor(data)
        fetched_pages += 1

        for row in rows:
            if not isinstance(row, dict):
                continue
            key = str(row.get("id") if row.get("id") is not None else row.get("jobUuid"))
            if key in seen:
                continue
            seen.add(key)
            items.append(_task_view(row))

        has_data = cursor.get("hasData")
        if has_data is False or not rows:
            break

        next_cursor = cursor.get("nextId") if direction == "next" else cursor.get("preId")
        if next_cursor is None or next_cursor == current:
            warnings.append("任务队列游标未前进，已停止，避免重复拉取")
            break
        if fetched_pages >= max_pages:
            warnings.append(f"已达到 --max-pages={max_pages}，剩余记录未拉取")
            break
        current = next_cursor

    result = _task_result(
        items,
        cursor,
        body,
        requested={
            "all": True,
            "cursorId": args.cursor_id,
            "direction": direction,
            "size": size,
            "maxPages": max_pages,
            "fetchedPages": fetched_pages,
        },
    )
    return {
        "data": result,
        "warnings": warnings,
        "meta": runtime.client.last_meta.to_dict(),
    }
