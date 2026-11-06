# -*- coding: utf-8 -*-
"""命令执行期的依赖容器。"""

from __future__ import annotations

from dataclasses import dataclass

from .client import YingDaoClient
from .config import Config


@dataclass
class Runtime:
    config: Config
    client: YingDaoClient
    dry_run: bool = False
    quiet: bool = False
    show_secrets: bool = False
