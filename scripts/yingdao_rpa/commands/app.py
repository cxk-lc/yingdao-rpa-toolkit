# -*- coding: utf-8 -*-
"""`app` 子命令：应用列表与应用运行记录（接口文档 3.2 / 3.3）。"""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Any

from ..errors import ParamError
from ..runtime import Runtime
from ..utils import parse_datetime_text
from .job import APP_STATUS_NAMES

APP_LIST_PATH = "/oapi/app/open/query/list"
APP_RUN_LIST_PATH = "/oapi/app/open/query/use/record/list"

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100
DEFAULT_MAX_PAGES = 50


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("app", help="应用（列表 / 运行记录）")
    actions = parser.add_subparsers(dest="app_action", required=True, metavar="<动作>")

    listing = actions.add_parser("list", parents=[common], help="分页查询应用列表")
    listing.add_argument("--app-id", help="应用 ID（精确匹配）")
    listing.add_argument("--app-name", help="应用名称（模糊匹配）")
    listing.add_argument("--owner", help="应用所有者账号（精确匹配）")
    listing.add_argument("--page", type=int, help="页码，默认 1")
    listing.add_argument("--size", type=int, help=f"每页条数，默认 {DEFAULT_PAGE_SIZE}，最大 {MAX_PAGE_SIZE}")
    listing.add_argument("--all", action="store_true", help="自动翻页拉取全部结果")
    listing.add_argument("--max-pages", type=int, help=f"--all 时最多拉取页数，默认 {DEFAULT_MAX_PAGES}")
    listing.set_defaults(handler=run_list, command="app list")

    runs = actions.add_parser("runs", parents=[common], help="查询应用运行记录")
    runs.add_argument("--app-id", help="应用 ID；与时间筛选至少提供一个")
    runs.add_argument("--begin-date", help="开始时间，YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
    runs.add_argument("--end-date", help="结束时间，YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
    runs.add_argument("--min-id", type=int, help="游标起始 id，默认 0")
    runs.add_argument("--size", type=int, help=f"每页条数，默认 {DEFAULT_PAGE_SIZE}，最大 {MAX_PAGE_SIZE}")
    runs.add_argument("--all", action="store_true", help="按 minId 游标自动翻页")
    runs.add_argument("--max-pages", type=int, help=f"--all 时最多拉取页数，默认 {DEFAULT_MAX_PAGES}")
    runs.set_defaults(handler=run_runs, command="app runs")


def _page_size(value: int | None) -> int:
    size = value if value is not None else DEFAULT_PAGE_SIZE
    if not (1 <= size <= MAX_PAGE_SIZE):
        raise ParamError(f"--size 必须在 1~{MAX_PAGE_SIZE} 之间，当前为：{size}")
    return size


def _max_pages(value: int | None) -> int:
    pages = value if value is not None else DEFAULT_MAX_PAGES
    if pages < 1:
        raise ParamError(f"--max-pages 必须大于等于 1，当前为：{pages}")
    return pages


def _time(value: str | None, field: str) -> str | None:
    try:
        return parse_datetime_text(value, field=field)
    except ValueError as exc:
        raise ParamError(str(exc)) from exc


def build_list_body(args: argparse.Namespace) -> tuple[dict[str, Any], int, int]:
    page = args.page if args.page is not None else 1
    size = _page_size(args.size)
    if page < 1:
        raise ParamError(f"--page 必须大于等于 1，当前为：{page}")

    body: dict[str, Any] = {"page": str(page), "size": str(size)}
    if args.app_id and args.app_id.strip():
        body["appId"] = args.app_id.strip()
    if args.app_name and args.app_name.strip():
        body["appName"] = args.app_name.strip()
    if args.owner and args.owner.strip():
        body["ownerUserSearchKey"] = args.owner.strip()
    return body, page, size


def build_runs_body(args: argparse.Namespace) -> tuple[dict[str, Any], int, int]:
    size = _page_size(args.size)
    min_id = args.min_id if args.min_id is not None else 0
    if min_id < 0:
        raise ParamError(f"--min-id 不能为负数，当前为：{min_id}")

    begin = _time(args.begin_date, "开始时间")
    end = _time(args.end_date, "结束时间")
    if not args.app_id and not begin and not end:
        raise ParamError(
            "查询运行记录需要 --app-id 或 --begin-date/--end-date 至少一个",
            hint="接口要求应用与时间筛选必传其中之一。",
        )
    if not args.app_id and not (begin and end):
        raise ParamError(
            "未提供 --app-id 时，必须同时提供 --begin-date 和 --end-date",
            hint="时间筛选需要完整的起止范围；也可以改用 --app-id 查询。",
        )
    if begin and end and begin > end:
        raise ParamError("开始时间不能晚于结束时间")
    if begin and end:
        start_at = datetime.strptime(begin, "%Y-%m-%d %H:%M:%S")
        end_at = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        if (end_at - start_at).total_seconds() > 7 * 86400:
            raise ParamError(
                "开始时间与结束时间跨度不能超过 7 天",
                hint="接口限制单次查询最多 7 天；请缩小范围或分段查询。",
            )

    body: dict[str, Any] = {"size": str(size), "minId": min_id}
    if args.app_id and args.app_id.strip():
        body["appId"] = args.app_id.strip()
    if begin:
        body["beginDate"] = begin
    if end:
        body["endDate"] = end
    return body, min_id, size


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, dict):
        data = data.get("dataList") or data.get("list") or []
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _page_info(payload: dict[str, Any]) -> dict[str, Any]:
    page = payload.get("page")
    return page if isinstance(page, dict) else {}


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _max_id(rows: list[dict[str, Any]]) -> int:
    values = [_to_int(row.get("id")) for row in rows]
    return max((value for value in values if value is not None), default=0)


def _result(items: list[dict[str, Any]], page: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "app_list",
        "items": items,
        "count": len(items),
        "page": page,
        "filters": {
            key: value for key, value in body.items() if key not in ("page", "size")
        },
        "requested": {
            "all": False,
            "page": _to_int(body["page"]),
            "size": _to_int(body["size"]),
        },
    }


def run_list(args: argparse.Namespace, runtime: Runtime) -> dict:
    body, page, size = build_list_body(args)
    max_pages = _max_pages(args.max_pages)

    if runtime.dry_run:
        return {
            "data": {
                "kind": "request_preview",
                "request": runtime.client.preview(
                    "POST", APP_LIST_PATH, body=body, show_secrets=runtime.show_secrets
                ),
                "requested": {
                    "all": args.all,
                    "maxPages": max_pages if args.all else None,
                },
            },
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    if not args.all:
        payload = runtime.client.request("POST", APP_LIST_PATH, body=body)
        return {
            "data": _result(_rows(payload), _page_info(payload), body),
            "meta": runtime.client.last_meta.to_dict(),
        }

    items: list[dict[str, Any]] = []
    page_info: dict[str, Any] = {}
    warnings: list[str] = []
    current = page
    fetched_pages = 0

    while True:
        page_body = dict(body)
        page_body["page"] = str(current)
        payload = runtime.client.request("POST", APP_LIST_PATH, body=page_body)
        rows = _rows(payload)
        items.extend(rows)
        page_info = _page_info(payload)
        fetched_pages += 1

        total_pages = _to_int(page_info.get("pages"))
        if total_pages is not None:
            if current >= total_pages:
                break
        elif len(rows) < size:
            break

        if fetched_pages >= max_pages:
            warnings.append(f"已达到 --max-pages={max_pages}，剩余页未拉取")
            break
        current += 1

    result = _result(items, page_info, body)
    result["requested"] = {
        "all": True,
        "page": page,
        "size": size,
        "maxPages": max_pages,
        "fetchedPages": fetched_pages,
    }
    return {
        "data": result,
        "warnings": warnings,
        "meta": runtime.client.last_meta.to_dict(),
    }


def _run_result(
    items: list[dict[str, Any]],
    page: dict[str, Any],
    body: dict[str, Any],
    *,
    next_min_id: int,
) -> dict[str, Any]:
    views: list[dict[str, Any]] = []
    for item in items:
        view = dict(item)
        status = str(view.get("runStatus") or "")
        view["statusName"] = APP_STATUS_NAMES.get(status, status)
        views.append(view)
    return {
        "kind": "app_run_list",
        "items": views,
        "count": len(views),
        "page": page,
        "nextMinId": next_min_id,
        "filters": {
            key: value for key, value in body.items() if key not in ("size", "minId")
        },
        "requested": {
            "all": False,
            "minId": _to_int(body["minId"]),
            "size": _to_int(body["size"]),
        },
    }


def run_runs(args: argparse.Namespace, runtime: Runtime) -> dict:
    body, min_id, size = build_runs_body(args)
    max_pages = _max_pages(args.max_pages)

    if runtime.dry_run:
        return {
            "data": {
                "kind": "request_preview",
                "request": runtime.client.preview(
                    "POST", APP_RUN_LIST_PATH, body=body, show_secrets=runtime.show_secrets
                ),
                "requested": {
                    "all": args.all,
                    "maxPages": max_pages if args.all else None,
                },
            },
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    if not args.all:
        payload = runtime.client.request("POST", APP_RUN_LIST_PATH, body=body)
        rows = _rows(payload)
        return {
            "data": _run_result(rows, _page_info(payload), body, next_min_id=_max_id(rows)),
            "meta": runtime.client.last_meta.to_dict(),
        }

    items: list[dict[str, Any]] = []
    page_info: dict[str, Any] = {}
    warnings: list[str] = []
    seen: set[str] = set()
    cursor = min_id
    last_max_id = min_id
    fetched_pages = 0

    while True:
        page_body = dict(body)
        page_body["minId"] = cursor
        payload = runtime.client.request("POST", APP_RUN_LIST_PATH, body=page_body)
        rows = _rows(payload)
        page_info = _page_info(payload)
        fetched_pages += 1

        new_count = 0
        for row in rows:
            key = str(row.get("id") if row.get("id") is not None else row.get("runRecordId"))
            if key in seen:
                continue
            seen.add(key)
            items.append(row)
            new_count += 1

        if not rows or len(rows) < size:
            last_max_id = _max_id(rows) or cursor
            break

        current_page = _to_int(page_info.get("page"))
        total_pages = _to_int(page_info.get("pages"))
        if current_page is not None and total_pages is not None and current_page >= total_pages:
            last_max_id = _max_id(rows) or cursor
            break

        next_cursor = _max_id(rows)
        last_max_id = next_cursor
        if next_cursor == cursor or new_count == 0:
            warnings.append("运行记录游标未前进，已停止，避免重复拉取")
            break
        if fetched_pages >= max_pages:
            warnings.append(f"已达到 --max-pages={max_pages}，剩余记录未拉取")
            break
        cursor = next_cursor

    result = _run_result(items, page_info, body, next_min_id=last_max_id)
    result["requested"] = {
        "all": True,
        "minId": min_id,
        "size": size,
        "maxPages": max_pages,
        "fetchedPages": fetched_pages,
    }
    return {
        "data": result,
        "warnings": warnings,
        "meta": runtime.client.last_meta.to_dict(),
    }
