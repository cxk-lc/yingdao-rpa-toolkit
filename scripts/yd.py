#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""影刀 RPA 工具包命令入口（薄壳）。

用法：
    python scripts/yd.py --version
    python scripts/yd.py config init
    python scripts/yd.py config show
    python scripts/yd.py auth check
    python scripts/yd.py job start --app-id <appId> --account-name <机器人名> --param 月份=2026-10
    python scripts/yd.py job query --job-uuid <uuid> --wait
"""

from __future__ import annotations

import sys
from pathlib import Path

# 让 `python scripts/yd.py` 在未安装包的情况下也能导入核心库
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:  # Windows 控制台默认不是 UTF-8，先统一编码
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover - 极老终端不支持
    pass

from yingdao_rpa.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
