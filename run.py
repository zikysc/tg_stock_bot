"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

"""

import sys
from pathlib import Path

# 解决 src layout 导入问题
root_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(root_dir))

from stock_bot.main import main

if __name__ == "__main__":
    main()
