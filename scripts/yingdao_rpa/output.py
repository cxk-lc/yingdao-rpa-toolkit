# -*- coding: utf-8 -*-
"""输出契约：stdout 永远是一条 JSON；text 仅供人读。

结构（成功）：
    {"schema_version":1,"ok":true,"command":"job start",...,
     "data":{...},"warnings":[],"meta":{...}}
结构（失败）：
    {"schema_version":1,"ok":false,"command":"...","error":{...},"data":null,...}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .errors import ToolError
from .utils import now_iso

SCHEMA_VERSION = 1

META_KEYS = ("base_url", "api_code", "api_success", "request_id", "dry_run")


def normalize_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    """把 meta 补齐为契约字段，缺失的键统一为 `None`。

    `--dry-run` 与本地命令未发请求，`api_code` / `api_success` / `request_id`
    在 JSON 中显式为 `null`，避免调用方因字段缺席而误判。
    """
    source = dict(meta or {})
    normalized = {key: source.pop(key, None) for key in META_KEYS}
    normalized.update(source)
    return normalized


def make_success(
    *,
    command: str,
    data: Any,
    warnings: list[str],
    meta: dict[str, Any],
    started_at: str,
    elapsed_ms: int,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": True,
        "command": command,
        "started_at": started_at,
        "finished_at": now_iso(),
        "elapsed_ms": elapsed_ms,
        "data": data,
        "warnings": warnings,
        "meta": meta,
    }


def make_error(
    *,
    command: str,
    error: ToolError,
    started_at: str,
    elapsed_ms: int,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "command": command,
        "started_at": started_at,
        "finished_at": now_iso(),
        "elapsed_ms": elapsed_ms,
        "error": error.to_dict(),
        "data": error.data,
        "warnings": warnings or [],
    }


def _render_preview(data: dict[str, Any]) -> str:
    """预览形态的人读输出：优先展示请求要素，不再落入各命令的常规渲染分支。"""
    request = data.get("request") or {}
    method = str(request.get("method") or "")
    target = request.get("url")
    action = "未写入文件" if method == "WRITE" else "未发送请求"
    lines = [f"[预览] {action}：{method} {target}"]

    query = request.get("query")
    if isinstance(query, dict) and query:
        lines.append("query=" + json.dumps(query, ensure_ascii=False))
    body = request.get("body")
    if body is not None:
        lines.append("body=" + json.dumps(body, ensure_ascii=False, indent=2))

    followup = data.get("followup")
    if isinstance(followup, dict):
        lines.append(
            f"后续请求：{followup.get('method')} {followup.get('url')} "
            f"body={json.dumps(followup.get('body'), ensure_ascii=False)}"
        )
    fallback = data.get("fallback")
    if fallback:
        lines.append("回退：" + json.dumps(fallback, ensure_ascii=False))
    return "\n".join(lines)


def render_text(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        error = payload.get("error") or {}
        lines = [f"✗ [{error.get('type', 'Error')}] {error.get('message', '')}"]
        if error.get("hint"):
            lines.append(f"  提示：{error['hint']}")
        if error.get("request_id"):
            lines.append(f"  requestId：{error['request_id']}")
        data = payload.get("data")
        if isinstance(data, dict) and data.get("job"):
            job = data["job"] or {}
            lines.append(f"  任务状态：{job.get('status')}（{job.get('statusName') or '-'}）")
        return "\n".join(lines)

    data = payload.get("data") or {}
    command = str(payload.get("command") or "")

    # 预览必须最先判定：否则会落入各命令的常规分支，出现"鉴权成功""无应用"等误导性文案
    if isinstance(data, dict) and data.get("kind") == "request_preview":
        return _render_preview(data)

    if command == "config show":
        keys = [
            "base_url",
            "access_key_id",
            "access_key_secret",
            "timeout_seconds",
            "poll_interval_seconds",
            "max_poll_seconds",
            "default_account_name",
            "default_robot_client_group_uuid",
            "enterprise_suffix",
            "source",
            "config_path",
        ]
        return "\n".join(f"{key}={data.get(key) if data.get(key) not in (None, '') else '-'}" for key in keys)

    if command == "config init":
        return f"已生成配置模板：{data.get('path')}（scope={data.get('scope')}）"

    if command == "auth check":
        expires = data.get("expires_in")
        expires_text = f"{expires}s" if expires is not None else "-"
        return (
            f"鉴权成功  base_url={data.get('base_url') or '-'}  "
            f"expires_in={expires_text}  source={data.get('source') or '-'}  "
            f"token={data.get('token_masked') or '-'}"
        )

    if command == "auth token":
        # 该命令的 purpose 就是输出可直接传递的 token 原文，便于 shell 管道消费
        return str(data.get("access_token") or "")

    if command == "app list":
        items = data.get("items") or []
        lines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"[{item.get('appTypeName') or item.get('appType') or '应用'}] "
                f"{item.get('appName') or '-'}（{item.get('appId') or '-'}）  "
                f"版本={item.get('version') or '-'}  "
                f"所有者={item.get('ownerName') or '-'}"
                f"（{item.get('ownerAccount') or '-'}）  "
                f"参数={'支持' if item.get('supportParam') else '不支持'}  "
                f"更新={item.get('updateTime') or '-'}"
            )
        if not lines:
            lines.append("（无应用）")
        page = data.get("page") or {}
        if page.get("total") is not None:
            lines.append(f"共 {page.get('total')} 个应用；本次已拉取 {len(items)} 个")
        return "\n".join(lines)

    if command == "app runs":
        items = data.get("items") or []
        lines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"[{item.get('runStatusName') or item.get('statusName') or item.get('runStatus') or '-'}] "
                f"{item.get('appName') or '-'}  "
                f"开始={item.get('startTime') or '-'}  "
                f"结束={item.get('endTime') or '-'}  "
                f"耗时={item.get('runningTime') if item.get('runningTime') is not None else '-'}s  "
                f"触发={item.get('startModeName') or item.get('startMode') or '-'}  "
                f"账号={item.get('userName') or '-'}"
                + (f"  remark={item['remark']}" if item.get("remark") else "")
            )
        if not lines:
            lines.append("（无运行记录）")
        page = data.get("page") or {}
        if page.get("total") is not None:
            lines.append(f"共 {page.get('total')} 条；本次已拉取 {len(items)} 条")
        return "\n".join(lines)

    if command == "robot tasks":
        items = data.get("items") or []
        lines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"[{item.get('statusName') or item.get('status') or '-'}] "
                f"{item.get('robotName') or '-'} / {item.get('taskName') or '-'}  "
                f"触发={item.get('triggerTime') or '-'}  "
                f"开始={item.get('startTime') or '-'}  "
                f"结束={item.get('endTime') or '-'}  "
                f"机器人={item.get('robotClientName') or '-'}  "
                f"job={item.get('jobUuid') or '-'}"
                + (f"  remark={item['remark']}" if item.get("remark") else "")
            )
        if not lines:
            lines.append("（无任务记录）")
        cursor = data.get("cursor") or {}
        if cursor:
            lines.append(
                f"hasData={cursor.get('hasData')}  nextId={cursor.get('nextId')}  "
                f"preId={cursor.get('preId')}"
            )
        return "\n".join(lines)

    if command == "account list":
        items = data.get("items") or []
        lines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"[{item.get('accountTypeName') or item.get('accountType') or '-'}] "
                f"{item.get('name') or '-'}（{item.get('loginAccount') or '-'}）  "
                f"手机={item.get('phone') or '-'}  "
                f"角色={item.get('roleName') or item.get('role') or '-'}  "
                f"最近登录={item.get('latestLoginTime') or '-'}  "
                f"过期={item.get('expiredTime') or '-'}"
            )
        if not lines:
            lines.append("（无账号）")
        page = data.get("page") or {}
        total = page.get("total")
        if total is not None:
            lines.append(f"共 {total} 条；本次已拉取 {len(items)} 条")
        return "\n".join(lines)

    if command == "robot info":
        robot = data.get("robot") or {}
        requested = data.get("requested") or {}
        parts = [
            f"[{robot.get('statusName') or robot.get('status') or '-'}]",
            str(robot.get("robotClientName") or requested.get("accountName") or "-"),
            f"ip={robot.get('clientIp') or '-'}",
            f"uuid={robot.get('robotClientUuid') or '-'}",
            f"备注={robot.get('description') or '-'}",
        ]
        if robot.get("remark"):
            parts.append(f"remark={robot['remark']}")
        if requested.get("resolvedBy") == "account":
            parts.append("（已通过企业账号补全）")
        elif requested.get("resolvedBy") == "suffix":
            parts.append("（已补全企业后缀）")
        return "  ".join(parts)

    if command.startswith("job"):
        job = data.get("job") or {}
        if job:
            parts = [
                f"jobUuid={job.get('jobUuid') or data.get('jobUuid') or '-'}",
                f"status={job.get('status') or '-'}",
                f"statusName={job.get('statusName') or '-'}",
            ]
            if job.get("robotName"):
                parts.append(f"应用={job['robotName']}")
            if job.get("robotClientName"):
                parts.append(f"机器人={job['robotClientName']}")
            if job.get("remark"):
                parts.append(f"remark={job['remark']}")
            return "  ".join(parts)
        if data.get("jobUuid"):
            return f"jobUuid={data['jobUuid']}  idempotent={data.get('idempotentFlag')}"

    return json.dumps(payload, ensure_ascii=False, indent=2)


def emit(payload: dict[str, Any], fmt: str = "json", save_path: str | None = None) -> None:
    if fmt == "text":
        print(render_text(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if save_path:
        target = Path(save_path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    for warning in payload.get("warnings") or []:
        print(f"warning: {warning}", file=sys.stderr)
