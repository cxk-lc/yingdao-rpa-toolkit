# -*- coding: utf-8 -*-
"""日志：只写 stderr 与可选文件，绝不污染 stdout 的 JSON。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

LOGGER_NAME = "yingdao_rpa"
_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def setup_logging(level: str = "warning", log_file: str | None = None) -> logging.Logger:
    """配置根 logger；重复调用会先清空旧 handler，避免测试间串味。"""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(_LEVELS.get(level.lower(), logging.WARNING))
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    if log_file:
        target = Path(log_file).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(target, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.debug("日志文件：%s", target)

    return logger


def get_logger(suffix: str | None = None) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{suffix}" if suffix else LOGGER_NAME)
