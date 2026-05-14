"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.
"""

from telegram import Update
from telegram.ext import ContextTypes

from src.stock_bot.config.settings import CONFIG
from src.stock_bot.infrastructure.stock_api import StockAPI
from src.stock_bot.utils.logger import setup_logger

logger = setup_logger('commands.basic')


def _get_id_key(item: dict):
    """获取历史记录的 ID 字段名（record_id 或 id）"""
    if 'record_id' in item:
        return 'record_id'
    if 'id' in item:
        return 'id'
    return None


async def _clear_old_history(api: StockAPI, keep_count: int = 5) -> int:
    """清理旧历史记录，返回实际清理数量"""
    try:
        response = await api.get_history(limit=100)

        if isinstance(response, dict):
            history = response.get('items', [])
        else:
            history = response if isinstance(response, list) else []

        logger.info(f'获取历史记录: 共 {len(history)} 条')

        if not history:
            logger.warning('get_history 返回空列表')
            return 0

        id_key = _get_id_key(history[0])
        if not id_key:
            logger.error('无法找到 record_id 或 id 字段')
            return 0

        # 按 ID 倒序（最新在前）
        history.sort(key=lambda x: x.get(id_key, 0) if isinstance(x, dict) else 0, reverse=True)

        cleaned_count = 0

        if len(history) > keep_count:
            old_ids = [x.get(id_key) for x in history[keep_count:] if isinstance(x, dict) and x.get(id_key)]

            logger.info(f'准备删除 {len(old_ids)} 条旧记录')

            if old_ids:
                await api.delete_history(old_ids)
                cleaned_count = len(old_ids)
                logger.info(f'✅ 成功清理 {cleaned_count} 条记录')
        else:
            logger.info(f'当前只有 {len(history)} 条记录，未达到清理阈值 ({keep_count} 条)')

        return cleaned_count

    except Exception as e:
        logger.error(f'清理历史记录时发生异常: {e}', exc_info=True)
        return 0


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    api: StockAPI = context.bot_data['api']
    response = await api.get_history(limit=100)

    if isinstance(response, dict):
        history = response.get('items', [])
        total = response.get('total', len(history))
    else:
        history = response if isinstance(response, list) else []
        total = len(history)

    if not history:
        return await update.message.reply_text('📭 还没有历史记录，说明你还没开始交学费。')

    # 获取排序用的 id_key
    id_key = None

    try:
        if history and isinstance(history[0], dict):
            id_key = _get_id_key(history[0])
    except Exception as e:
        logger.warning(f'get_id_key 获取失败: {e}')

    # 排序
    if id_key:
        try:
            history.sort(key=lambda x: x.get(id_key, 0) if isinstance(x, dict) else 0, reverse=True)
        except Exception as sort_e:
            logger.warning(f'history 排序失败: {sort_e}')

    lines = []

    for h in history:
        if not isinstance(h, dict):
            continue

        code = h.get('stock_code', 'N/A')
        name = h.get('stock_name', '未知')
        score = h.get('sentiment_score')
        advice = h.get('operation_advice', '')

        score_str = f' | 情绪{score}分' if score is not None else ''
        advice_str = f' | {advice}' if advice else ''

        lines.append(f'• `{code}` {name}{score_str}{advice_str}')

    msg = f'📋 **历史分析记录 ({total} 条):**\n' + '\n'.join(lines[:40])

    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None, silent=False):
    api: StockAPI = context.bot_data['api']

    cleaned = await _clear_old_history(api, CONFIG['keep_count'])

    if not silent:
        if cleaned > 0:
            await update.message.reply_text(f'🧹 已清理 {cleaned} 条旧记录，历史已从系统中抹去。')
        else:
            await update.message.reply_text(f'✨ 当前只有 {cleaned} 条记录，还不够成为故事。')
