# -*- coding: utf-8 -*-
"""异常到退出码的稳定映射，以及失败时仍保留业务数据。"""

from __future__ import annotations

import pytest

from yingdao_rpa.errors import (
    ApiError,
    AuthError,
    ConfigError,
    JobFailedError,
    NetworkError,
    ParamError,
    PollTimeoutError,
    PreconditionError,
    ToolError,
)
from yingdao_rpa.utils import mask_secret, redact_mapping


@pytest.mark.parametrize(
    ("error", "exit_code", "kind"),
    [
        (ToolError("x"), 1, "ToolError"),
        (ApiError("x"), 1, "ApiError"),
        (ParamError("x"), 2, "ParamError"),
        (ConfigError("x"), 2, "ConfigError"),
        (AuthError("x"), 3, "AuthError"),
        (NetworkError("x"), 4, "NetworkError"),
        (PollTimeoutError("x"), 4, "TimeoutError"),
        (JobFailedError("x"), 5, "JobFailedError"),
        (PreconditionError("x"), 6, "PreconditionError"),
    ],
)
def test_exit_code_contract(error, exit_code, kind):
    assert error.exit_code == exit_code
    assert error.to_dict()["type"] == kind


def test_error_dict_contains_diagnostic_fields():
    error = ApiError("调用失败", code=500, request_id="req-1", hint="稍后重试")

    assert error.to_dict() == {
        "type": "ApiError",
        "code": 500,
        "message": "调用失败",
        "hint": "稍后重试",
        "request_id": "req-1",
    }


def test_job_failure_keeps_business_data():
    job = {"status": "error", "remark": "元素未找到"}

    error = JobFailedError("任务失败", data={"job": job})

    assert error.data["job"]["remark"] == "元素未找到"


def test_mask_secret_short_and_long():
    assert mask_secret("") == ""
    assert mask_secret("short") == "****"
    assert mask_secret("EBCgDuVc1m5k") == "EBCg****1m5k"


def test_redact_mapping_hides_sensitive_keys():
    result = redact_mapping({"accessKeySecret": "s", "token": "t", "baseUrl": "u"})

    assert result == {"accessKeySecret": "***", "token": "***", "baseUrl": "u"}
