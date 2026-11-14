# -*- coding: utf-8 -*-
"""机器人调度选择规则。

规则：
1. 用户指定机器人时优先使用；非空闲则返回决策请求（排队 / 改派）。
2. 未指定机器人时优先空闲；多个空闲优先历史成功次数最多，否则随机。
"""

from __future__ import annotations

import secrets
from typing import Any, Callable

from .errors import ApiError, PreconditionError, ToolError
from .logging_setup import get_logger

ROBOT_LIST_PATH = "/oapi/dispatch/v2/client/list"
ROBOT_QUERY_PATH = "/oapi/dispatch/v2/client/query"
JOB_LIST_PATH = "/oapi/dispatch/v2/job/list"

ROBOT_STATUS_NAMES = {
    "connected": "已连接",
    "idle": "空闲",
    "allocated": "已分配",
    "running": "运行中",
    "offline": "离线",
}
BUSY_ONLINE_STATUSES = frozenset({"connected", "allocated", "running"})
IDLE = "idle"
ROBOT_PAGE_SIZE = 100
ROBOT_MAX_PAGES = 20
HISTORY_PAGE_SIZE = 100
HISTORY_MAX_PAGES = 5

logger = get_logger("scheduling")


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _robot_view(robot: dict[str, Any], success_count: int | None = None) -> dict[str, Any]:
    view = dict(robot)
    status = str(view.get("status") or "")
    view["statusName"] = ROBOT_STATUS_NAMES.get(status, status)
    view["accountName"] = str(view.get("robotClientName") or "")
    if success_count is not None:
        view["successCount"] = success_count
    return view


def _selection(
    robot: dict[str, Any],
    reason: str,
    *,
    success_count: int = 0,
    idle_candidates: int = 0,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "accountName": str(robot.get("robotClientName") or ""),
        "robotClientUuid": robot.get("robotClientUuid"),
        "status": robot.get("status"),
        "statusName": robot.get("statusName"),
        "reason": reason,
        "successCount": success_count,
        "idleCandidates": idle_candidates,
        "warnings": warnings or [],
    }


def list_robots(
    client: Any,
    *,
    status: str | None = None,
    key: str | None = None,
    group_uuid: str | None = None,
    page_size: int = ROBOT_PAGE_SIZE,
    max_pages: int = ROBOT_MAX_PAGES,
) -> list[dict[str, Any]]:
    """分页查询机器人列表（4.4）。"""
    robots: list[dict[str, Any]] = []
    page = 1
    while page <= max_pages:
        body: dict[str, Any] = {"page": page, "size": page_size}
        if status:
            body["status"] = status
        if key:
            body["key"] = key
        if group_uuid:
            body["robotClientGroupUuid"] = group_uuid
        payload = client.request("POST", ROBOT_LIST_PATH, body=body)
        data = payload.get("data")
        rows = data if isinstance(data, list) else []
        robots.extend(_robot_view(row) for row in rows if isinstance(row, dict))

        page_info = payload.get("page") if isinstance(payload.get("page"), dict) else {}
        total_pages = _to_int(page_info.get("pages"))
        if total_pages is not None:
            if page >= total_pages:
                break
        elif len(rows) < page_size:
            break
        page += 1
    return robots


def find_robot(client: Any, app_id: str, account_name: str) -> dict[str, Any]:
    """按 accountName 查询单台机器人（4.2）。"""
    try:
        payload = client.request(
            "POST", ROBOT_QUERY_PATH, body={"accountName": account_name}
        )
    except ApiError as exc:
        if "未查询到机器人" in exc.message or "未找到" in exc.message:
            raise PreconditionError(
                "未查询到指定机器人",
                request_id=exc.request_id,
                hint="确认机器人名称是否完整；也可以改用 --auto-robot 让工具选择空闲机器人。",
                data={
                    "kind": "dispatch_decision",
                    "reason": "robot_not_found",
                    "appId": app_id,
                    "requestedRobot": {"accountName": account_name},
                    "instructions": "请让用户确认机器人账号，或改用 --auto-robot。",
                },
            ) from exc
        raise

    data = payload.get("data")
    if not isinstance(data, dict) or not data:
        raise PreconditionError(
            "未查询到指定机器人",
            request_id=payload.get("requestId"),
            hint="确认机器人名称是否完整；也可以改用 --auto-robot 让工具选择空闲机器人。",
            data={
                "kind": "dispatch_decision",
                "reason": "robot_not_found",
                "appId": app_id,
                "requestedRobot": {"accountName": account_name},
                "instructions": "请让用户确认机器人账号，或改用 --auto-robot。",
            },
        )
    return _robot_view(data)


def count_successes(
    client: Any,
    app_id: str,
    *,
    max_pages: int = HISTORY_MAX_PAGES,
) -> tuple[dict[str, int], list[str]]:
    """统计该应用在各机器人上的历史成功次数（4.1，finish 状态）。

    只统计最近若干页，避免为了选一台机器人拉取全部历史。
    """
    counts: dict[str, int] = {}
    warnings: list[str] = []
    cursor: Any = None

    for page in range(max_pages):
        body: dict[str, Any] = {
            "robotUuid": app_id,
            "statusList": ["finish"],
            "size": HISTORY_PAGE_SIZE,
            "cursorDirection": "next",
        }
        if cursor is not None:
            body["cursorId"] = cursor
        try:
            payload = client.request("POST", JOB_LIST_PATH, body=body)
        except ToolError as exc:
            warnings.append(f"查询历史成功次数失败，改按随机空闲选择：{exc.message}")
            break

        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        rows = data.get("dataList") if isinstance(data.get("dataList"), list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            uuid = str(row.get("robotClientUuid") or "").strip()
            name = str(row.get("robotClientName") or "").strip()
            if uuid:
                counts[uuid] = counts.get(uuid, 0) + 1
            if name:
                counts[name] = counts.get(name, 0) + 1

        if not data.get("hasData"):
            break
        next_id = data.get("nextId")
        if next_id is None or next_id == cursor:
            break
        cursor = next_id
    else:
        warnings.append(f"历史成功次数仅统计最近 {max_pages} 页")

    return counts, warnings


def _success_count(robot: dict[str, Any], counts: dict[str, int]) -> int:
    for key in (robot.get("robotClientUuid"), robot.get("robotClientName")):
        if key and str(key) in counts:
            return counts[str(key)]
    return 0


def _candidates(robots: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    result = [
        _robot_view(robot, success_count=_success_count(robot, counts))
        for robot in robots
    ]
    return sorted(
        result,
        key=lambda item: (-int(item.get("successCount") or 0), str(item.get("accountName") or "")),
    )


def _safe_idle_robots(client: Any) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        return list_robots(client, status=IDLE), []
    except ToolError as exc:
        return [], [f"查询空闲机器人失败，候选列表可能不完整：{exc.message}"]


def _safe_successes(client: Any, app_id: str) -> tuple[dict[str, int], list[str]]:
    try:
        return count_successes(client, app_id)
    except ToolError as exc:  # pragma: no cover - count_successes 已内部兜底
        return {}, [f"查询历史成功次数失败，改按随机空闲选择：{exc.message}"]


def select_robot(
    client: Any,
    app_id: str,
    *,
    account_name: str | None = None,
    queue_if_busy: bool = False,
    chooser: Callable[[list[dict[str, Any]]], dict[str, Any]] = secrets.choice,
) -> dict[str, Any]:
    """按调度规则选择机器人；无法自动决定时抛 PreconditionError。"""
    if account_name:
        robot = find_robot(client, app_id, account_name)
        status = str(robot.get("status") or "")

        if status == IDLE:
            return _selection(robot, "specified_idle", idle_candidates=1)

        if queue_if_busy:
            warnings = []
            if status == "offline":
                warnings.append("机器人离线，任务可能排队到超时")
            return _selection(
                robot,
                "specified_queue",
                idle_candidates=0,
                warnings=warnings,
            )

        idle, warnings = _safe_idle_robots(client)
        counts, history_warnings = _safe_successes(client, app_id)
        warnings.extend(history_warnings)
        candidates = _candidates(idle, counts)
        decision = {
            "kind": "dispatch_decision",
            "reason": "specified_robot_busy",
            "appId": app_id,
            "requestedRobot": robot,
            "idleCandidates": candidates,
            "queueOption": {
                "accountName": robot.get("robotClientName"),
                "robotClientUuid": robot.get("robotClientUuid"),
                "status": status,
                "statusName": robot.get("statusName"),
                "flag": "--queue-if-busy",
            },
            "instructions": (
                "请询问用户：1) 排队等待：重跑原命令并加 --queue-if-busy；"
                "2) 改派：从 idleCandidates 选择 accountName，重跑时替换 --account-name。"
            ),
            "warnings": warnings,
        }
        raise PreconditionError(
            "指定的机器人当前不是空闲状态",
            hint="请询问用户选择「排队等待」或「改派」，详见 data.idleCandidates。",
            data=decision,
        )

    idle = list_robots(client, status=IDLE)
    if idle:
        counts, warnings = _safe_successes(client, app_id)
        candidates = _candidates(idle, counts)
        if len(candidates) == 1:
            selected = candidates[0]
            return _selection(
                selected,
                "auto_only_idle",
                success_count=int(selected.get("successCount") or 0),
                idle_candidates=1,
                warnings=warnings,
            )

        max_count = max(int(item.get("successCount") or 0) for item in candidates)
        if max_count > 0:
            pool = [
                item for item in candidates if int(item.get("successCount") or 0) == max_count
            ]
            reason = "auto_most_success"
        else:
            pool = candidates
            reason = "auto_random"
        selected = chooser(pool)
        return _selection(
            selected,
            reason,
            success_count=int(selected.get("successCount") or 0),
            idle_candidates=len(candidates),
            warnings=warnings,
        )

    all_robots = list_robots(client)
    online = [
        robot
        for robot in all_robots
        if str(robot.get("status") or "") in BUSY_ONLINE_STATUSES
    ]
    counts, warnings = _safe_successes(client, app_id)
    candidates = _candidates(online, counts)

    if candidates:
        raise PreconditionError(
            "当前没有空闲机器人",
            hint="请询问用户是否从 onlineCandidates 选择一台机器人排队，或稍后重试。",
            data={
                "kind": "dispatch_decision",
                "reason": "no_idle_robot",
                "appId": app_id,
                "onlineCandidates": candidates,
                "instructions": (
                    "当前没有空闲机器人；请询问用户是否从 onlineCandidates 选择一台排队。"
                    "重跑时加 --account-name <选中账号> --queue-if-busy。"
                ),
                "warnings": warnings,
            },
        )

    raise PreconditionError(
        "当前没有可用机器人",
        hint="确认机器人已接入调度模式；也可以稍后重试。",
        data={
            "kind": "dispatch_decision",
            "reason": "no_available_robot",
            "appId": app_id,
            "robots": all_robots,
            "instructions": "没有处于在线状态的机器人；请检查机器人客户端与调度模式。",
            "warnings": warnings,
        },
    )
