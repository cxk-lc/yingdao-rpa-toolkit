# -*- coding: utf-8 -*-
"""子命令注册表。

新增命令的固定动作：
1. 在本目录新建模块，实现 register(subparsers, common) 与 run(args, runtime)；
2. 把模块加入下面的 MODULES 元组；
3. 在 tests/ 补一条 CLI 契约用例。
"""

from __future__ import annotations

import argparse

from . import account, app, auth, config_cmd, job, robot

MODULES = (account, app, auth, config_cmd, job, robot)


def register_all(
    subparsers: argparse._SubParsersAction, common: argparse.ArgumentParser
) -> None:
    for module in MODULES:
        module.register(subparsers, common)
