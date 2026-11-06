# -*- coding: utf-8 -*-
"""`account` 子命令：查询 RPA 企业账号（接口文档 2.2）。"""

from __future__ import annotations

import argparse
from typing import Any

from ..errors import ParamError
from ..runtime import Runtime
from ..utils import parse_timestamp

ACCOUNT_LIST_PATH = "/oapi/rpa/user/v1/list"
ACCOUNT_TYPES = ("basic", "senior")
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_MAX_PAGES = 50


def register(subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser("account", help="RPA 企业账号")
    actions = parser.add_subparsers(dest="account_action", required=True, metavar="<动作>")

    listing = actions.add_parser("list", parents=[common], help="分页查询 RPA 企业账号")
    listing.add_argument("--keyword", help="账号关键词")
    listing.add_argument("--phone", help="完整手机号")
    listing.add_argument(
        "--account-type",
        action="append",
        metavar="TYPE",
        help="账号类型 basic / senior，可重复或逗号分隔",
    )
    listing.add_argument("--latest-login-begin", help="最近登录时间起点：秒级时间戳或 YYYY-MM-DD [HH:MM:SS]")
    listing.add_argument("--latest-login-end", help="最近登录时间终点")
    listing.add_argument("--expired-begin", help="过期时间起点")
    listing.add_argument("--expired-end", help="过期时间终点")
    listing.add_argument("--page", type=int, help="页码，默认 1")
    listing.add_argument("--size", type=int, help=f"每页条数，默认 {DEFAULT_PAGE_SIZE}，最大 {MAX_PAGE_SIZE}")
    listing.add_argument("--all", action="store_true", help="自动翻页拉取全部结果")
    listing.add_argument("--max-pages", type=int, help=f"--all 时最多拉取页数，默认 {DEFAULT_MAX_PAGES}")
    listing.set_defaults(handler=run_list, command="account list")


def _parse_types(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for raw in values or []:
        for item in str(raw).split(","):
            name = item.strip().lower()
            if not name:
                continue
            if name not in ACCOUNT_TYPES:
                raise ParamError(
                    f"未知账号类型：{item}",
                    hint=f"可选值：{' / '.join(ACCOUNT_TYPES)}；可重复或逗号分隔。",
                )
            if name not in result:
                result.append(name)
    return result


def _timestamp(value: str | None, field: str) -> int | None:
    try:
        return parse_timestamp(value, field=field)
    except ValueError as exc:
        raise ParamError(str(exc)) from exc


def _time_pair(begin: int | None, end: int | None, label: str) -> None:
    if begin is not None and end is not None and begin > end:
        raise ParamError(f"{label}的起点不能晚于终点")


def build_query(args: argparse.Namespace) -> dict[str, Any]:
    page = args.page if args.page is not None else 1
    size = args.size if args.size is not None else DEFAULT_PAGE_SIZE
    if page < 1:
        raise ParamError(f"--page 必须大于等于 1，当前为：{page}")
    if not (1 <= size <= MAX_PAGE_SIZE):
        raise ParamError(f"--size 必须在 1~{MAX_PAGE_SIZE} 之间，当前为：{size}")

    query: dict[str, Any] = {"page": page, "size": size}
    if args.keyword and args.keyword.strip():
        query["accountKeyword"] = args.keyword.strip()
    if args.phone and args.phone.strip():
        query["phone"] = args.phone.strip()

    types = _parse_types(args.account_type)
    if types:
        query["accountTypes"] = types

    latest_begin = _timestamp(args.latest_login_begin, "最近登录时间起点")
    latest_end = _timestamp(args.latest_login_end, "最近登录时间终点")
    _time_pair(latest_begin, latest_end, "最近登录时间")
    if latest_begin is not None:
        query["latestLoginTimeBegin"] = latest_begin
    if latest_end is not None:
        query["latestLoginTimeEnd"] = latest_end

    expired_begin = _timestamp(args.expired_begin, "过期时间起点")
    expired_end = _timestamp(args.expired_end, "过期时间终点")
    _time_pair(expired_begin, expired_end, "过期时间")
    if expired_begin is not None:
        query["expiredTimeBegin"] = expired_begin
    if expired_end is not None:
        query["expiredTimeEnd"] = expired_end

    return query


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


def _result(items: list[dict[str, Any]], page: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "account_list",
        "items": items,
        "count": len(items),
        "page": page,
        "filters": {key: value for key, value in query.items() if key not in ("page", "size")},
        "requested": {"all": False, "page": query["page"], "size": query["size"]},
    }


def run_list(args: argparse.Namespace, runtime: Runtime) -> dict:
    query = build_query(args)
    max_pages = args.max_pages if args.max_pages is not None else DEFAULT_MAX_PAGES
    if args.all and max_pages < 1:
        raise ParamError(f"--max-pages 必须大于等于 1，当前为：{max_pages}")

    if runtime.dry_run:
        return {
            "data": {
                "kind": "request_preview",
                "request": runtime.client.preview(
                    "GET", ACCOUNT_LIST_PATH, query=query, show_secrets=runtime.show_secrets
                ),
                "requested": {"all": args.all, "maxPages": max_pages if args.all else None},
            },
            "meta": {"base_url": runtime.config.base_url, "dry_run": True},
        }

    if not args.all:
        payload = runtime.client.request("GET", ACCOUNT_LIST_PATH, query=query)
        return {
            "data": _result(_rows(payload), _page_info(payload), query),
            "meta": runtime.client.last_meta.to_dict(),
        }

    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    page_info: dict[str, Any] = {}
    page = query["page"]
    fetched_pages = 0

    while True:
        page_query = dict(query)
        page_query["page"] = page
        payload = runtime.client.request("GET", ACCOUNT_LIST_PATH, query=page_query)
        rows = _rows(payload)
        items.extend(rows)
        page_info = _page_info(payload)
        fetched_pages += 1

        total_pages = _to_int(page_info.get("pages"))
        if total_pages is not None:
            if page >= total_pages:
                break
        elif len(rows) < query["size"]:
            break

        if fetched_pages >= max_pages:
            warnings.append(f"已达到 --max-pages={max_pages}，剩余页未拉取")
            break
        page += 1

    result = _result(items, page_info, query)
    result["requested"] = {
        "all": True,
        "page": query["page"],
        "size": query["size"],
        "maxPages": max_pages,
        "fetchedPages": fetched_pages,
    }
    return {
        "data": result,
        "warnings": warnings,
        "meta": runtime.client.last_meta.to_dict(),
    }
