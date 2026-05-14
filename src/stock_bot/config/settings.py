"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Dispatcher: 负责加载和管理配置项
"""

import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('STOCK_API_URL')
STOCK_PASSWORD = os.getenv('STOCK_API_PASSWORD')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

CONFIG = {'keep_count': 5}
