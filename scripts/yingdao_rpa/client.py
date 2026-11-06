# -*- coding: utf-8 -*-
"""影刀开放 API 客户端。

职责边界：
- 管理 accessToken 生命周期（获取、进程内复用、401 刷新）；
- **不把 token 写入磁盘**：token 只存在于当前进程内存，跨命令通过参数传递；
- 统一判定 `success` 字段，并把失败映射成本项目的异常；
- 处理 429 退避；
- 不关心具体业务命令，命令层只提交 path/body 并消费 `data`。
"""

from __future__ import annotations

import json
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

from .config import Config, require_credentials
from .errors import (
    AUTH_HINT,
    ApiError,
    AuthError,
    NetworkError,
)
from .logging_setup import get_logger
from .transport import HttpTransport, RawResponse, encode_json_body

TOKEN_PATH = "/oapi/token/v2/token/create"
MAX_429_RETRIES = 3

EXTERNAL_TOKEN_HINT = (
    "请重新执行 `auth token` 获取新 token，再通过 --access-token 或 "
    "YD_ACCESS_TOKEN 传给需要调用的命令。"
)

logger = get_logger("client")


@dataclass
class TokenInfo:
    access_token: str
    expires_in: int
    expires_at: float
    source: str  # fetched（凭据换取） / external（调用方传入）


@dataclass
class ApiMeta:
    base_url: str
    api_code: int | None = None
    api_success: bool = False
    request_id: str | None = None
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "api_code": self.api_code,
            "api_success": self.api_success,
            "request_id": self.request_id,
            "dry_run": self.dry_run,
        }


class YingDaoClient:
    def __init__(
        self,
        config: Config,
        transport: HttpTransport | None = None,
        access_token: str = "",
        sleep: Any = None,
    ) -> None:
        self.config = config
        self.transport = transport or HttpTransport(config.timeout_seconds)
        self._sleep = sleep or time.sleep
        # 调用方传入的 token 优先使用；它只在内存里，不落盘、不写日志
        self._token = (access_token or "").strip()
        self._token_source = "external" if self._token else ""
        self._token_expires_at = float("inf") if self._token else 0.0
        self.last_meta = ApiMeta(base_url=config.base_url)

    # ---------------------------------------------------------------- 鉴权
    def create_token(self) -> TokenInfo:
        """用 accessKeyId/accessKeySecret 换取 token；只更新内存，不写文件。"""
        require_credentials(self.config)
        payload = self.request(
            "GET",
            TOKEN_PATH,
            query={
                "accessKeyId": self.config.access_key_id,
                "accessKeySecret": self.config.access_key_secret,
            },
            need_token=False,
            retry_401=False,
        )
        data = payload.get("data") or {}
        token = data.get("accessToken")
        if not token:
            raise AuthError(
                "鉴权响应缺少 accessToken",
                request_id=payload.get("requestId"),
                hint=AUTH_HINT,
            )

        expires_in = int(data.get("expiresIn") or 7200)
        self._token = str(token)
        # 按官方 expiresIn 计算内存过期时间，留 30 秒安全边界
        self._token_expires_at = time.time() + max(expires_in - 30, 0)
        self._token_source = "fetched"
        logger.debug("已获取 accessToken（expires_in=%s，仅内存持有）", expires_in)

        return TokenInfo(
            access_token=self._token,
            expires_in=expires_in,
            expires_at=self._token_expires_at,
            source="fetched",
        )

    def token_info(self) -> TokenInfo:
        """返回当前可用 token；有传入或已获取且未过期时直接复用。"""
        if self._token and time.time() < self._token_expires_at:
            if self._token_source == "external":
                return TokenInfo(
                    access_token=self._token,
                    expires_in=0,
                    expires_at=0.0,
                    source="external",
                )
            return TokenInfo(
                access_token=self._token,
                expires_in=max(0, int(self._token_expires_at - time.time())),
                expires_at=self._token_expires_at,
                source="fetched",
            )
        return self.create_token()

    def token(self) -> str:
        return self.token_info().access_token

    # ------------------------------------------------------------ 请求封装
    def _decode(self, raw: RawResponse, path: str) -> dict[str, Any]:
        try:
            payload = json.loads(raw.text)
        except json.JSONDecodeError as exc:
            snippet = (raw.text or "").strip()[:300]
            if raw.status == 401:
                raise AuthError(
                    f"HTTP 401：{snippet or '无响应体'}",
                    code=401,
                    hint=AUTH_HINT,
                ) from exc
            raise NetworkError(
                f"响应不是合法 JSON（HTTP {raw.status}）：{snippet}",
                code=raw.status,
            ) from exc
        if not isinstance(payload, dict):
            raise NetworkError(f"响应顶层不是 JSON 对象（{path}）", code=raw.status)
        return payload

    def _raise_business_error(self, payload: dict[str, Any]) -> None:
        message = str(payload.get("msg") or "调用失败")
        code = payload.get("code")
        request_id = payload.get("requestId")
        lowered = message.lower()
        if code in (401, 403) or "accesskey" in lowered or "token" in lowered or "未授权" in message:
            raise AuthError(message, code=code, request_id=request_id, hint=AUTH_HINT)
        raise ApiError(message, code=code, request_id=request_id)

    def _backoff_seconds(self, raw: RawResponse, attempt: int) -> float:
        retry_after = next(
            (value for key, value in raw.headers.items() if key.lower() == "retry-after"),
            None,
        )
        if retry_after:
            try:
                return max(1.0, float(retry_after))
            except ValueError:
                pass
        return float(2**attempt)

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        need_token: bool = True,
        retry_401: bool = True,
        retry_429: bool = True,
    ) -> dict[str, Any]:
        url = self.config.base_url + path
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        attempts_429 = 0
        refreshed = False

        while True:
            headers = {"Accept": "application/json"}
            data = None
            if body is not None:
                data = encode_json_body(body)
                headers["Content-Type"] = "application/json"
            if need_token:
                headers["Authorization"] = f"Bearer {self.token()}"

            logger.debug("请求 %s %s", method.upper(), path)
            raw = self.transport.request(
                method.upper(),
                url,
                headers=headers,
                body=data,
                timeout=self.config.timeout_seconds,
            )
            logger.debug(
                "响应 %s %s -> HTTP %s（%sms）",
                method.upper(),
                path,
                raw.status,
                raw.elapsed_ms,
            )
            payload = self._decode(raw, path)

            if raw.status == 429 or payload.get("code") == 429:
                if retry_429 and attempts_429 < MAX_429_RETRIES:
                    attempts_429 += 1
                    delay = self._backoff_seconds(raw, attempts_429)
                    logger.warning("触发限流（429），%.1f 秒后第 %d 次重试", delay, attempts_429)
                    self._sleep(delay)
                    continue
                raise ApiError(
                    payload.get("msg") or "触发接口限流（429）",
                    code=payload.get("code") or 429,
                    request_id=payload.get("requestId"),
                    hint="请降低请求频率后重试；批量翻页时减小 size。",
                )

            if raw.status == 401 or payload.get("code") == 401:
                if need_token and retry_401 and not refreshed:
                    if self._token_source == "external":
                        # 调用方显式传入的 token 被视为权威，不擅自换成凭据换取的新 token
                        raise AuthError(
                            "传入的 accessToken 已失效",
                            code=payload.get("code") or 401,
                            request_id=payload.get("requestId"),
                            hint=EXTERNAL_TOKEN_HINT,
                        )
                    refreshed = True
                    logger.info("accessToken 已失效，重新获取后重试一次")
                    self.create_token()
                    continue
                raise AuthError(
                    payload.get("msg") or "接口未授权（401）",
                    code=payload.get("code") or 401,
                    request_id=payload.get("requestId"),
                    hint=AUTH_HINT,
                )

            success = payload.get("success")
            if success is None:
                # 个别列表接口用 code=0/200 表示成功，不返回 success 字段
                success = payload.get("code") in (0, 200)
            if not success:
                self._raise_business_error(payload)

            self.last_meta = ApiMeta(
                base_url=self.config.base_url,
                api_code=payload.get("code"),
                api_success=True,
                request_id=payload.get("requestId"),
            )
            return payload

    # ------------------------------------------------------------ 干跑预览
    def preview(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        need_token: bool = True,
    ) -> dict[str, Any]:
        """构造请求预览（不发送），密钥字段脱敏。"""
        safe_query = {
            key: ("***" if "secret" in key.lower() else value)
            for key, value in (query or {}).items()
        }
        preview: dict[str, Any] = {
            "method": method.upper(),
            "url": self.config.base_url + path,
            "query": safe_query,
            "body": body,
        }
        if need_token:
            preview["headers"] = {"Authorization": "Bearer <accessToken>"}
        return preview
