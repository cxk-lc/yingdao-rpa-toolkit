# -*- coding: utf-8 -*-
"""异常体系与退出码映射。

退出码是 CLI 与调用方之间的稳定契约：
    0 成功 / 1 接口或业务错误 / 2 参数或配置 / 3 鉴权
    4 网络或超时 / 5 任务终态失败 / 6 前置条件不满足
"""

from __future__ import annotations

from typing import Any


class ToolError(Exception):
    """工具包所有异常的基类。"""

    kind = "ToolError"
    exit_code = 1

    def __init__(
        self,
        message: str,
        *,
        code: Any = None,
        request_id: str | None = None,
        hint: str | None = None,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.request_id = request_id
        self.hint = hint
        # 失败时仍值得返回给调用方的业务数据（如失败任务的最终状态）
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.kind,
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "request_id": self.request_id,
        }

    def __str__(self) -> str:  # pragma: no cover - 仅用于兜底打印
        return self.message


class ParamError(ToolError):
    """本地参数校验失败，未发出任何请求。"""

    kind = "ParamError"
    exit_code = 2


class ConfigError(ToolError):
    """配置缺失或格式错误。"""

    kind = "ConfigError"
    exit_code = 2


class AuthError(ToolError):
    """凭据错误、token 失效或权限不足。"""

    kind = "AuthError"
    exit_code = 3


class ApiError(ToolError):
    """接口返回 success=false，或 HTTP 状态异常。"""

    kind = "ApiError"
    exit_code = 1


class NetworkError(ToolError):
    """网络不可达、超时，或响应不是合法 JSON。"""

    kind = "NetworkError"
    exit_code = 4


class PollTimeoutError(ToolError):
    """轮询等待超过上限，任务仍未进入终态。"""

    kind = "TimeoutError"
    exit_code = 4


class JobFailedError(ToolError):
    """任务进入非 finish 的终态。"""

    kind = "JobFailedError"
    exit_code = 5


class PreconditionError(ToolError):
    """当前状态不满足操作前提（如重试非失败任务）。"""

    kind = "PreconditionError"
    exit_code = 6


AUTH_HINT = (
    "请核对 accessKeyId / accessKeySecret 是否正确、是否已被禁用，"
    "以及 base_url 是否为 API 域名（公有云 https://api.yingdao.com，专有云为专属域名）。"
)

CONFIG_HINT = (
    "请在影刀控制台由企业管理员进入「高级设置 → API 配置」创建 accessKeyId / accessKeySecret，"
    "然后执行 `python scripts/yd.py config init` 生成模板并填写。"
)
