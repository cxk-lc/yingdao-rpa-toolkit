# -*- coding: utf-8 -*-
"""客户端：鉴权头、业务错误映射、401 刷新、429 退避。

全部使用假传输层，不触网。
"""

from __future__ import annotations

import json

import pytest

from yingdao_rpa.client import YingDaoClient
from yingdao_rpa.errors import ApiError, AuthError, NetworkError
from yingdao_rpa.token_store import TokenStore
from yingdao_rpa.transport import RawResponse

TOKEN_PAYLOAD = {
    "success": True,
    "code": 200,
    "data": {"accessToken": "tok-1", "expiresIn": 7200},
}


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def request(self, method, url, headers=None, body=None, timeout=None):
        self.calls.append(
            {"method": method, "url": url, "headers": headers or {}, "body": body, "timeout": timeout}
        )
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_client(fake_config, tmp_path, responses, sleeps=None):
    store = TokenStore(path=tmp_path / "cache.json", enabled=False)
    transport = FakeTransport(responses)
    captured = sleeps if sleeps is not None else []

    def fake_sleep(seconds):
        captured.append(seconds)

    client = YingDaoClient(fake_config, transport=transport, store=store, sleep=fake_sleep)
    return client, transport, captured


def test_request_adds_bearer_and_returns_payload(fake_config, response_factory, tmp_path):
    client, transport, _ = make_client(
        fake_config,
        tmp_path,
        [
            response_factory(200, TOKEN_PAYLOAD),
            response_factory(200, {"success": True, "code": 200, "data": {"jobUuid": "j-1"}}),
        ],
    )

    payload = client.request("POST", "/oapi/dispatch/v2/job/query", body={"jobUuid": "j-1"})

    assert payload["data"]["jobUuid"] == "j-1"
    assert transport.calls[0]["url"].startswith("https://example.test/oapi/token/v2/token/create?")
    assert transport.calls[1]["headers"]["Authorization"] == "Bearer tok-1"
    assert json.loads(transport.calls[1]["body"]) == {"jobUuid": "j-1"}
    assert client.last_meta.api_code == 200
    assert client.last_meta.api_success is True


def test_business_failure_maps_to_api_error(fake_config, response_factory, tmp_path):
    client, _, _ = make_client(
        fake_config,
        tmp_path,
        [
            response_factory(200, TOKEN_PAYLOAD),
            response_factory(200, {"success": False, "code": 500, "msg": "机器人不存在", "requestId": "r-9"}),
        ],
    )

    with pytest.raises(ApiError) as excinfo:
        client.request("POST", "/x", body={})

    assert excinfo.value.code == 500
    assert excinfo.value.request_id == "r-9"


def test_401_refreshes_token_once(fake_config, response_factory, tmp_path):
    client, transport, _ = make_client(
        fake_config,
        tmp_path,
        [
            response_factory(200, TOKEN_PAYLOAD),
            response_factory(401, {"success": False, "code": 401, "msg": "token expired"}),
            response_factory(200, {**TOKEN_PAYLOAD, "data": {"accessToken": "tok-2", "expiresIn": 7200}}),
            response_factory(200, {"success": True, "code": 200, "data": {"ok": True}}),
        ],
    )

    payload = client.request("POST", "/x", body={})

    assert payload["data"]["ok"] is True
    assert len(transport.calls) == 4
    assert transport.calls[3]["headers"]["Authorization"] == "Bearer tok-2"


def test_401_without_token_is_auth_error(fake_config, response_factory, tmp_path):
    client, _, _ = make_client(
        fake_config,
        tmp_path,
        [response_factory(401, {"success": False, "code": 401, "msg": "bad accessKey"})],
    )

    with pytest.raises(AuthError):
        client.request("GET", "/oapi/token/v2/token/create", need_token=False)


def test_429_uses_retry_after_header(fake_config, response_factory, tmp_path):
    client, transport, sleeps = make_client(
        fake_config,
        tmp_path,
        [
            response_factory(200, TOKEN_PAYLOAD),
            response_factory(429, {"success": False, "code": 429, "msg": "too many"}, {"Retry-After": "2"}),
            response_factory(200, {"success": True, "code": 200, "data": {"ok": True}}),
        ],
    )

    payload = client.request("POST", "/x", body={})

    assert payload["success"] is True
    assert sleeps == [2.0]
    assert len(transport.calls) == 3


def test_non_json_response_maps_to_network_error(fake_config, tmp_path):
    client, _, _ = make_client(
        fake_config,
        tmp_path,
        [RawResponse(status=502, text="<html>bad gateway</html>")],
    )

    with pytest.raises(NetworkError, match="不是合法 JSON"):
        client.request("GET", "/x", need_token=False)


def test_cached_token_skips_token_request(fake_config, response_factory, tmp_path):
    store = TokenStore(path=tmp_path / "cache.json", enabled=True)
    transport = FakeTransport([response_factory(200, {"success": True, "code": 200, "data": {}})])
    client = YingDaoClient(fake_config, transport=transport, store=store)
    store.put(client._cache_key(), "cached-token", expires_at=9_999_999_999)

    client.request("POST", "/x", body={})

    assert len(transport.calls) == 1
    assert transport.calls[0]["headers"]["Authorization"] == "Bearer cached-token"


def test_preview_masks_secret_query(fake_config):
    client = YingDaoClient(fake_config, store=TokenStore(enabled=False))

    preview = client.preview("GET", "/token", query={"accessKeySecret": "secret", "id": "1"})

    assert preview["query"]["accessKeySecret"] == "***"
    assert preview["query"]["id"] == "1"
