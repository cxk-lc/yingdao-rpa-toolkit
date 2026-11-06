# -*- coding: utf-8 -*-
"""accessToken 跨进程缓存。

缓存只是加速手段：任何读写失败都退化为“无缓存”，不影响主流程。
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

CACHE_VERSION = 1


def default_cache_path() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        base = Path(os.environ["LOCALAPPDATA"])
    else:
        base = Path.home() / ".cache"
    return base / "yingdao-rpa-toolkit" / "token-cache.json"


def _expires_at(entry: Any) -> float:
    if not isinstance(entry, dict):
        return 0.0
    try:
        return float(entry.get("expiresAt", 0))
    except (TypeError, ValueError):
        return 0.0


class TokenStore:
    def __init__(self, path: Path | None = None, enabled: bool = True) -> None:
        self.path = Path(path) if path else default_cache_path()
        self.enabled = enabled

    def _load(self) -> dict[str, Any]:
        if not self.enabled or not self.path.is_file():
            return {"version": CACHE_VERSION, "entries": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": CACHE_VERSION, "entries": {}}
        if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
            return {"version": CACHE_VERSION, "entries": {}}
        return data

    def _write(self, data: dict[str, Any]) -> None:
        if not self.enabled:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
            temp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temp, self.path)
            if os.name != "nt":
                os.chmod(self.path, 0o600)
        except OSError:
            # 缓存写入失败不影响主流程
            return

    def get(self, key: str) -> dict[str, Any] | None:
        data = self._load()
        entry = data["entries"].get(key)
        if not isinstance(entry, dict):
            return None
        expires_at = _expires_at(entry)
        if expires_at <= time.time() or not entry.get("accessToken"):
            return None
        entry["expiresAt"] = expires_at
        return entry

    def put(
        self,
        key: str,
        access_token: str,
        expires_at: float,
        *,
        base_url: str = "",
        key_id_tail: str = "",
    ) -> None:
        if not self.enabled:
            return
        data = self._load()
        now = time.time()
        entries = {
            name: entry
            for name, entry in data["entries"].items()
            if _expires_at(entry) > now
        }
        entries[key] = {
            "accessToken": access_token,
            "expiresAt": expires_at,
            "obtainedAt": now,
            "baseUrl": base_url,
            "keyIdTail": key_id_tail,
        }
        data["version"] = CACHE_VERSION
        data["entries"] = entries
        self._write(data)

    def invalidate(self, key: str) -> None:
        if not self.enabled:
            return
        data = self._load()
        if data["entries"].pop(key, None) is not None:
            self._write(data)
