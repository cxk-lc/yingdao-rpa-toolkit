# -*- coding: utf-8 -*-
"""影刀开放 API 客户端。

职责边界：
- 管理 accessToken 生命周期（获取、缓存、401 刷新）；
- 统一判定 `success` 字段，并把失败映射成本项目的异常；
- 处理 429 退避；
- 不关心具体业务命令，命令层只提交 path/body 并消费 `data`。
"""

from __future__ import annotations

import hashlib
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
from .token_store import TokenStore
from .transport import HttpTransport, RawResponse, encode_json_body

TOKEN_PATH = "/oapi/token/v2/token/create"
MAX_429_RETRIES = 3

logger = get_logger("client")


@dataclass
class TokenInfo:
    access_token: str
    expires_in: int
    expires_at: float
    cached: bool


@dataclass
class ApiMeta:
    base_url: str
    api_code: int | None = None
    api_success: bool = False
    request_id: str | None = None
    token_cached: bool = False
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "api_code": self.api_code,
            "api_success": self.api_success,
            "request_id": self.request_id,
            "token_cached": self.token_cached,
            "dry_run": self.dry_run,
        }


class YingDaoClient:
    def __init__(
        self,
        config: Config,
        transport: HttpTransport | None = None,
        store: TokenStore | None = None,
        sleep: Any = None,
    ) -> None:
        self.config = config
        self.transport = transport or HttpTransport(config.timeout_seconds)
        self.store = store if store is not None else TokenStore(enabled=config.token_cache_enabled)
        self._sleep = sleep or time.sleep
        self._token = ""
        self._token_expires_at = 0.0
        self._token_cached = False
        self.last_meta = ApiMeta(base_url=config.base_url)

    # ---------------------------------------------------------------- 鉴权
    def _cache_key(self) -> str:
        raw = f"{self.config.base_url}|{self.config.access_key_id}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def create_token(self, force: bool = False) -> TokenInfo:
        require_credentials(self.config)
        key = self._cache_key()
        now = time.time()

        if not force:
            entry = self.store.get(key)
            if entry:
                self._token = str(entry["accessToken"])
                self._token_expires_at = float(entry["expiresAt"])
                self._token_cached = True
                logger.debug("复用缓存的 accessToken（expires_at=%s）", self._token_expires_at)
                return TokenInfo(
                    access_token=self._token,
                    expires_in=max(0, int(self._token_expires_at - now)),
                    expires_at=self._token_expires_at,
                    cached=True,
                )

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
        # 官方要求按 expiresIn 缓存，不要自定义缓存时长；留 30 秒安全边界
        self._token_expires_at = now + max(expires_in - 30, 0)
        self._token_cached = False
        logger.debug("已获取 accessToken（expires_in=%s）", expires_in)

        if expires_in >= 60:
            self.store.put(
                key,
                self._token,
                self._token_expires_at,
                base_url=self.config.base_url,
                key_id_tail=self.config.access_key_id[-6:],
            )

        return TokenInfo(
            access_token=self._token,
            expires_in=expires_in,
            expires_at=self._token_expires_at,
            cached=False,
        )

    def token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token
        return self.create_token().access_token

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
                    refreshed = True
                    logger.info("accessToken 已失效，强制刷新后重试一次")
                    self.create_token(force=True)
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
                token_cached=self._token_cached,
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
