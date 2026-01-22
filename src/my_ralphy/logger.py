"""日志管理模块"""

import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler


def setup_logger(
    name: str = "ralph",
    log_file: Optional[str] = "ralph.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，None 则不写文件
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已有的处理器
    logger.handlers.clear()

    # 日志格式
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rich 控制台处理器
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
    )
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# 全局日志实例
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取全局日志实例"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def init_logger(log_file: Optional[str] = "ralph.log", level: int = logging.INFO) -> logging.Logger:
    """初始化全局日志实例"""
    global _logger
    _logger = setup_logger(log_file=log_file, level=level)
    return _logger
