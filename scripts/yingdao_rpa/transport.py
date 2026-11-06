# -*- coding: utf-8 -*-
"""HTTP 传输层：只依赖标准库，可被测试替身整体替换。

这一层只负责“把请求发出去、把响应原样拿回来”：
- 网络层异常统一转成 NetworkError；
- HTTP 4xx/5xx 不在这里抛异常，交给 client 结合响应体判断业务语义。
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .errors import NetworkError


@dataclass
class RawResponse:
    """一次 HTTP 往返的原始结果。"""

    status: int
    text: str
    headers: dict[str, str] = field(default_factory=dict)
    elapsed_ms: int = 0


class HttpTransport:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        timeout: float | None = None,
    ) -> RawResponse:
        request = urllib.request.Request(
            url,
            data=body,
            headers=headers or {},
            method=method.upper(),
        )
        started = time.monotonic()
        effective_timeout = timeout or self.timeout
        try:
            with urllib.request.urlopen(request, timeout=effective_timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
                return RawResponse(
                    status=int(response.status),
                    text=text,
                    headers=dict(response.headers.items()),
                    elapsed_ms=int((time.monotonic() - started) * 1000),
                )
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            return RawResponse(
                status=int(exc.code),
                text=text,
                headers=dict(exc.headers.items()) if exc.headers else {},
                elapsed_ms=int((time.monotonic() - started) * 1000),
            )
        except urllib.error.URLError as exc:
            raise NetworkError(f"网络请求失败：{exc.reason}") from exc
        except (socket.timeout, TimeoutError) as exc:
            raise NetworkError(f"网络请求超时（{effective_timeout} 秒）") from exc
        except OSError as exc:
            raise NetworkError(f"网络请求失败：{exc}") from exc


def encode_json_body(body: Any) -> bytes:
    return json.dumps(body, ensure_ascii=False).encode("utf-8")
