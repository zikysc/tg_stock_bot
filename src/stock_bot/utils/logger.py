"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Dispatcher: 日志系统配置，支持控制台输出和按天归档文件
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = 'stock_bot'):
    """配置日志系统：控制台 + 按天归档文件，保留3天"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 创建 logs 目录
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 文件输出 - 按天归档，保留3天
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / 'stock_bot.log',
        when='midnight',  # 每天午夜切割
        interval=1,
        backupCount=3,  # 保留最近3天日志
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = '%Y-%m-%d.log'  # 文件名后缀
    logger.addHandler(file_handler)

    # 降低 httpx 和 telegram 的日志等级，避免刷屏
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    logger.info(f'🚀 日志系统初始化完成 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    return logger
