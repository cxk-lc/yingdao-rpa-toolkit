# -*- coding: utf-8 -*-
"""`job` 子命令：启动应用运行、查询运行结果。

两个高频约定写在最前面：
1. `robotUuid` 是 **应用 uuid（appId）**，不是机器人 uuid；
2. 接口成功（success=true）不等于任务成功，任务成功看终态 `finish`。
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable

from ..config import Config
from ..errors import JobFailedError, ParamError, PollTimeoutError
from ..logging_setup import get_logger
from ..runtime import Runtime
from ..scheduling import ROBOT_LIST_PATH, select_robot

START_PATH = "/oapi/dispatch/v2/job/start"
QUERY_PATH = "/oapi/dispatch/v2/job/query"

logger = get_logger("job")

TERMINAL_STATUSES = frozenset({"finish", "stopped", "error", "skipped", "cancel"})
APP_STATUS_NAMES = {
    "created": "已创建",
    "waiting": "等待调度",
    "running": "运行中",
    "finish": "完成",
    "stopping": "停止中",
    "stopped": "已停止",
    "error": "异常",
    "skipped": "已跳过",
    "cancel": "已取消",
}
APP_STATUS_CODES = tuple(APP_STATUS_NAMES)
PARAM_TYPES = frozenset({"str", "int", "float", "bool", "file"})
MAX_PARAMS_CHARS = 8000
PRIORITIES = ("high", "middle", "low")
EXECUTE_SCOPES = ("any", "all")


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("job", help="应用运行（启动 / 查询）")
    actions = parser.add_subparsers(dest="job_action", required=True, metavar="<动作>")

    start = actions.add_parser("start", parents=[common], help="启动一次应用运行")
    start.add_argument(
        "--app-id",
        "--robot-uuid",
        dest="app_id",
        required=True,
        help="应用 uuid（即接口的 robotUuid，不是机器人 uuid）",
    )
    start.add_argument("--account-name", help="机器人名称（省略时按配置默认值或自动选择；与分组二选一）")
    start.add_argument("--robot-group-uuid", help="机器人分组 uuid（与 --account-name 二选一）")
    start.add_argument(
        "--auto-robot",
        action="store_true",
        help="显式强制自动选择机器人（未指定账号/分组时默认就是自动）",
    )
    start.add_argument(
        "--queue-if-busy",
        action="store_true",
        help="指定机器人非空闲时允许排队；默认返回决策请求，由调用方询问用户",
    )
    start.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE[:TYPE]",
        help="应用参数，可重复；TYPE 取 str/int/float/bool/file，默认 str",
    )
    start.add_argument("--params-file", help="参数 JSON 文件（对象或 {name,value,type} 数组）")
    start.add_argument("--idempotent-uuid", help="幂等 uuid，长度不超过 36 位")
    start.add_argument("--priority", choices=PRIORITIES, help="排队优先级，默认 middle")
    start.add_argument("--wait-timeout-seconds", type=int, help="排队等待超时（60~950400 秒）")
    start.add_argument("--run-timeout", type=int, help="运行超时（60~950400 秒，需客户端 5.10+）")
    start.add_argument("--execute-scope", choices=EXECUTE_SCOPES, help="分组执行范围 any / all")
    start.add_argument("--wait", action="store_true", help="启动后轮询到终态")
    start.add_argument("--interval", type=int, help="轮询间隔秒数，默认取配置 pollIntervalSeconds")
    start.add_argument("--max-wait", type=int, help="最长等待秒数，默认取配置 maxPollSeconds")
    start.set_defaults(handler=run_start, command="job start")

    query = actions.add_parser("query", parents=[common], help="按 jobUuid 查询运行结果")
    query.add_argument("--job-uuid", required=True, help="启动接口返回的 jobUuid")
    query.add_argument("--wait", action="store_true", help="轮询到终态再返回")
    query.add_argument("--interval", type=int, help="轮询间隔秒数，默认取配置 pollIntervalSeconds")
    query.add_argument("--max-wait", type=int, help="最长等待秒数，默认取配置 maxPollSeconds")
    query.set_defaults(handler=run_query, command="job query")


# ---------------------------------------------------------------- 参数解析
def _parse_param(raw: str) -> dict[str, str]:
    name, sep, rest = raw.partition("=")
    if not sep or not name.strip():
        raise ParamError(
            f"应用参数格式应为 NAME=VALUE[:TYPE]：{raw!r}",
            hint='例如 --param 月份=2026-10 或 --param 页数=10:int。',
        )
    value = rest
    value_type = "str"
    tail, sep2, candidate = rest.rpartition(":")
    if sep2 and candidate in PARAM_TYPES:
        value, value_type = tail, candidate
    return {"name": name.strip(), "value": value, "type": value_type}


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else str(value)


def _load_params_file(path: str) -> list[dict[str, str]]:
    target = Path(path).expanduser()
    if not target.is_file():
        raise ParamError(f"参数文件不存在：{target}")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ParamError(f"参数文件无法解析：{target}", hint=str(exc)) from exc

    if isinstance(data, dict):
        return [{"name": str(key), "value": _stringify(value), "type": "str"} for key, value in data.items()]
    if not isinstance(data, list):
        raise ParamError("参数文件顶层必须是对象或数组", hint='数组元素形如 {"name":"月份","value":"2026-10"}。')

    params: list[dict[str, str]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict) or not item.get("name"):
            raise ParamError(f"参数文件第 {index + 1} 项缺少 name")
        value_type = str(item.get("type") or "str")
        if value_type not in PARAM_TYPES:
            raise ParamError(f"参数文件第 {index + 1} 项 type 非法：{value_type}")
        params.append(
            {
                "name": str(item["name"]),
                "value": _stringify(item.get("value")),
                "type": value_type,
            }
        )
    return params


def build_params(args: argparse.Namespace) -> list[dict[str, str]]:
    params = [_parse_param(raw) for raw in (args.param or [])]
    if args.params_file:
        params.extend(_load_params_file(args.params_file))
    if not params:
        return []

    names = [item["name"] for item in params]
    duplicated = sorted({name for name in names if names.count(name) > 1})
    if duplicated:
        raise ParamError(f"参数名重复：{', '.join(duplicated)}")

    encoded = json.dumps(params, ensure_ascii=False)
    if len(encoded) > MAX_PARAMS_CHARS:
        raise ParamError(
            f"参数总长度 {len(encoded)} 字符，超过 {MAX_PARAMS_CHARS} 字符上限",
            hint="请拆批调用，或把长文本转成文件类型（type=file）后传 URL。",
        )
    return params


def _check_range(value: int | None, name: str, minimum: int = 60, maximum: int = 950400) -> None:
    if value is None:
        return
    if not (minimum <= value <= maximum):
        raise ParamError(f"{name} 必须在 {minimum}~{maximum} 之间，当前为：{value}")


def _poll_settings(args: argparse.Namespace, config: Config) -> tuple[int, int]:
    interval = args.interval if args.interval is not None else config.poll_interval_seconds
    max_wait = args.max_wait if args.max_wait is not None else config.max_poll_seconds
    if interval < 5:
        raise ParamError(f"--interval 不能小于 5 秒，当前为：{interval}")
    if max_wait < 1:
        raise ParamError(f"--max-wait 必须大于 0 秒，当前为：{max_wait}")
    return interval, max_wait


def _resolve_target(args: argparse.Namespace, config: Config) -> tuple[str, str]:
    auto = bool(getattr(args, "auto_robot", False))
    if auto:
        if args.account_name or args.robot_group_uuid:
            raise ParamError(
                "--auto-robot 不能与 --account-name / --robot-group-uuid 同时使用",
                hint="自动模式会自行选择空闲机器人；如需指定目标，请去掉 --auto-robot。",
            )
        return "", ""

    if args.account_name and args.robot_group_uuid:
        raise ParamError(
            "--account-name 与 --robot-group-uuid 互斥，只能提供一个",
            hint="去掉其中一个后重试。",
        )
    if args.account_name and args.account_name.strip():
        return args.account_name.strip(), ""
    if args.robot_group_uuid and args.robot_group_uuid.strip():
        return "", args.robot_group_uuid.strip()

    account = (config.default_account_name or "").strip()
    group = (config.default_robot_client_group_uuid or "").strip()
    if account and group:
        raise ParamError(
            "配置里的 defaultAccountName 与 defaultRobotClientGroupUuid 互斥",
            hint="清掉其中一个，或用 --account-name / --robot-group-uuid / --auto-robot 显式指定。",
        )
    return account, group


def build_start_body(
    args: argparse.Namespace,
    config: Config,
    *,
    resolved_account: str | None = None,
) -> dict[str, Any]:
    account, group = _resolve_target(args, config)
    if resolved_account is not None:
        account = resolved_account
        group = ""
    _check_range(args.wait_timeout_seconds, "--wait-timeout-seconds")
    _check_range(args.run_timeout, "--run-timeout")

    body: dict[str, Any] = {"robotUuid": args.app_id}
    if account:
        body["accountName"] = account
    elif group:
        body["robotClientGroupUuid"] = group

    if args.idempotent_uuid:
        if len(args.idempotent_uuid) > 36:
            raise ParamError("idempotentUuid 长度不能超过 36 位")
        body["idempotentUuid"] = args.idempotent_uuid
    if args.priority:
        body["priority"] = args.priority
    if args.wait_timeout_seconds is not None:
        body["waitTimeoutSeconds"] = args.wait_timeout_seconds
    if args.run_timeout is not None:
        body["runTimeout"] = args.run_timeout
    if args.execute_scope:
        body["executeScope"] = args.execute_scope

    params = build_params(args)
    if params:
        body["params"] = params
    return body


# ---------------------------------------------------------------- 查询与轮询
def query_once(client: Any, job_uuid: str) -> dict[str, Any]:
    payload = client.request("POST", QUERY_PATH, body={"jobUuid": job_uuid})
    data = payload.get("data")
    if not isinstance(data, dict):
        raise JobFailedError(
            "查询接口未返回任务数据",
            request_id=payload.get("requestId"),
            hint="确认 jobUuid 是否属于当前企业、当前环境。",
        )
    return data


def poll_job(
    client: Any,
    job_uuid: str,
    *,
    interval: int,
    max_wait: int,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    deadline = time.monotonic() + max_wait
    attempts = 0
    while True:
        attempts += 1
        job = query_once(client, job_uuid)
        status = str(job.get("status") or "")
        logger.info("轮询任务 %s：第 %d 次，状态=%s", job_uuid, attempts, status or "unknown")
        if status in TERMINAL_STATUSES:
            return job
        if time.monotonic() >= deadline:
            raise PollTimeoutError(
                f"等待 {max_wait} 秒后任务仍未进入终态（当前 {status or '未知'}）",
                data={"jobUuid": job_uuid, "job": job, "attempts": attempts},
                hint="可稍后用 `job query --job-uuid ...` 再查，或检查机器人是否离线。",
            )
        sleep(interval)


def _split_failure(job: dict[str, Any], job_uuid: str) -> None:
    status = str(job.get("status") or "")
    if status in TERMINAL_STATUSES and status != "finish":
        raise JobFailedError(
            f"应用运行结束，状态：{status}（{job.get('statusName') or '-'}）",
            request_id=None,
            data={"kind": "job", "jobUuid": job_uuid, "job": job},
            hint="查看 remark 与 screenshotUrl 定位失败原因；确认可重试后再发起重试。",
        )


# ------------------------------------------------------------------ 命令体
def _preview_start(body: dict[str, Any], runtime: Runtime) -> dict:
    return {
        "data": {
            "kind": "request_preview",
            "request": runtime.client.preview(
                "POST", START_PATH, body=body, show_secrets=runtime.show_secrets
            ),
        },
        "meta": {"base_url": runtime.config.base_url, "dry_run": True},
    }


def _preview_auto_start(args: argparse.Namespace, runtime: Runtime) -> dict:
    base_body = build_start_body(args, runtime.config, resolved_account="")
    followup_body = dict(base_body)
    followup_body["accountName"] = "<selected-account>"
    return {
        "data": {
            "kind": "request_preview",
            "resolution": "auto-robot",
            "request": runtime.client.preview(
                "POST",
                ROBOT_LIST_PATH,
                body={"status": "idle", "page": 1, "size": 100},
                show_secrets=runtime.show_secrets,
            ),
            "followup": {
                "method": "POST",
                "url": runtime.config.base_url + START_PATH,
                "body": followup_body,
            },
            "requested": {"mode": "auto", "queueIfBusy": False},
        },
        "meta": {"base_url": runtime.config.base_url, "dry_run": True},
    }


def run_start(args: argparse.Namespace, runtime: Runtime) -> dict:
    account, _group = _resolve_target(args, runtime.config)
    auto = bool(getattr(args, "auto_robot", False)) or not (account or _group)
    queue_if_busy = bool(getattr(args, "queue_if_busy", False))

    if queue_if_busy:
        if auto:
            raise ParamError(
                "--queue-if-busy 不能用于自动选择模式",
                hint="自动模式只选择空闲机器人；如需排队，请指定 --account-name 并加 --queue-if-busy。",
            )
        if not account:
            raise ParamError("--queue-if-busy 只能与 --account-name 一起使用")

    if runtime.dry_run:
        if auto:
            return _preview_auto_start(args, runtime)
        return _preview_start(build_start_body(args, runtime.config), runtime)

    dispatch: dict[str, Any] | None = None
    if auto:
        dispatch = select_robot(runtime.client, args.app_id)
        account = dispatch["accountName"]
    elif account:
        dispatch = select_robot(
            runtime.client,
            args.app_id,
            account_name=account,
            queue_if_busy=queue_if_busy,
        )
        account = dispatch["accountName"]

    body = build_start_body(
        args,
        runtime.config,
        resolved_account=account if dispatch else None,
    )
    payload = runtime.client.request("POST", START_PATH, body=body)
    data = payload.get("data") or {}
    job_uuid = data.get("jobUuid")
    result: dict[str, Any] = {
        "kind": "job_start",
        "jobUuid": job_uuid,
        "idempotentFlag": data.get("idempotentFlag"),
        "request_id": payload.get("requestId"),
    }
    if dispatch:
        result["dispatch"] = dispatch

    if args.wait:
        if not job_uuid:
            raise JobFailedError(
                "启动成功但响应缺少 jobUuid，无法继续等待",
                request_id=payload.get("requestId"),
            )
        interval, max_wait = _poll_settings(args, runtime.config)
        job = poll_job(
            runtime.client,
            str(job_uuid),
            interval=interval,
            max_wait=max_wait,
        )
        result["job"] = job
        _split_failure(job, str(job_uuid))

    return {"data": result, "meta": runtime.client.last_meta.to_dict()}


def run_query(args: argparse.Namespace, runtime: Runtime) -> dict:
    if runtime.dry_run:
        return {
            "data": {
                "kind": "request_preview",
                "request": runtime.client.preview(
                    "POST",
                    QUERY_PATH,
                    body={"jobUuid": args.job_uuid},
                    show_secrets=runtime.show_secrets,
                ),
            },
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    if args.wait:
        interval, max_wait = _poll_settings(args, runtime.config)
        job = poll_job(
            runtime.client,
            args.job_uuid,
            interval=interval,
            max_wait=max_wait,
        )
    else:
        job = query_once(runtime.client, args.job_uuid)

    data = {"kind": "job", "jobUuid": args.job_uuid, "job": job}
    _split_failure(job, args.job_uuid)
    return {"data": data, "meta": runtime.client.last_meta.to_dict()}
