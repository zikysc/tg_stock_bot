"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Dispatcher: 提供与股票数据相关的核心业务逻辑
"""


import logging
from src.stock_bot.infrastructure.stock_api import StockAPI

logger = logging.getLogger("stock_bot")

def get_id_key(item: dict):
    """获取历史记录的 ID 字段名（record_id 或 id）"""
    if 'record_id' in item:
        return 'record_id'
    if 'id' in item:
        return 'id'
    return None

async def clear_old_history(api: StockAPI, keep_count: int = 5) -> int:
    """清理历史记录，返回实际清理的数量"""
    try:
        history = await api.get_history(limit=100)
        logger.info(f"获取历史记录: 共 {len(history)} 条")

        if not history:
            logger.warning("get_history 返回空列表")
            return 0

        id_key = get_id_key(history[0])
        if not id_key:
            logger.error("无法找到 record_id 或 id 字段")
            return 0

        # 按 ID 降序排序（最新的在前面）
        history.sort(key=lambda x: x.get(id_key, 0), reverse=True)

        cleaned_count = 0

        if len(history) > keep_count:
            old_ids = [x.get(id_key) for x in history[keep_count:] if x.get(id_key)]
            logger.info(f"准备删除 {len(old_ids)} 条旧记录")

            if old_ids:
                await api.delete_history(old_ids)
                cleaned_count = len(old_ids)
                logger.info(f"✅ 成功清理 {cleaned_count} 条记录")
        else:
            logger.info(f"当前只有 {len(history)} 条记录，未达到清理阈值 ({keep_count} 条)")

        return cleaned_count

    except Exception as e:
        logger.error(f"清理历史记录时发生异常: {e}", exc_info=True)
        return 0
