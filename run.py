"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

"""

import sys
from pathlib import Path

# 添加项目 src 目录到路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))


def main():
    """延迟导入 main，避免 E402"""
    from stock_bot.main import main as run_bot

    run_bot()


if __name__ == '__main__':
    main()
