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
        return (
            f"鉴权成功  base_url={data.get('base_url')}  "
            f"expires_in={data.get('expires_in')}s  source={data.get('source')}  "
            f"token={data.get('token_masked')}"
        )

    if command == "auth token":
        # 该命令的 purpose 就是输出可直接传递的 token 原文，便于 shell 管道消费
        return str(data.get("access_token") or "")

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
        if requested.get("suffixApplied"):
            parts.append("（已按配置补全企业后缀）")
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

    if isinstance(data, dict) and data.get("kind") == "request_preview":
        request = data.get("request") or {}
        body = json.dumps(request.get("body"), ensure_ascii=False, indent=2)
        return f"{request.get('method')} {request.get('url')}\n{body}"

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
