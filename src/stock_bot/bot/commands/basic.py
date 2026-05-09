"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Description: 基本命令处理函数
"""

from telegram import Update
from telegram.ext import ContextTypes
from src.stock_bot.config.settings import CONFIG
from src.stock_bot.core.services import clear_old_history, get_id_key
from src.stock_bot.infrastructure.stock_api import StockAPI
from src.stock_bot.utils.logger import setup_logger

logger = setup_logger("commands.basic")

COMMAND_DOCS = {
    "help": "显示帮助菜单",
    "usage": "今日大模型 Token 消耗统计",
    "list": "查看个股历史分析记录",
    "price <代码>": "实时价格行情查询",
    "kline <代码>": "获取个股 K 线图",
    "clear": "清理个股分析历史记录",
    "market_review": "大盘分析任务",
    "<代码> <名称>": "个股深度分析"
}


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    bot_name = context.bot.username or "StockBot"
    help_text = "🤖 **当前版本还在‘成长中’，暂时只解锁了少量指令技能，其它功能正在路上，别急，它还在加班进化。**\n\n" + "\n".join([
        f"• `@{bot_name} {k}`: {v}" for k, v in COMMAND_DOCS.items()
    ])
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    api: StockAPI = context.bot_data['api']
    history = await api.get_history(limit=100) 
    if not history:
        return await update.message.reply_text("📭 还没有历史记录，说明你还没开始交学费。")
    
    id_key = get_id_key(history[0])
    if id_key:
        history.sort(key=lambda x: x.get(id_key, 0), reverse=True)
    
    lines = []
    for h in history:
        code = h.get('stock_code', 'N/A')
        name = h.get('stock_name', '未知')
        score = h.get('sentiment_score')
        advice = h.get('operation_advice', '')
        score_str = f" | 情绪{score}分" if score is not None else ""
        advice_str = f" | {advice}" if advice else ""
        lines.append(f"• `{code}` {name}{score_str}{advice_str}")
    
    msg = f"📋 **历史分析记录 ({len(history)} 条):**\n" + "\n".join(lines[:40])
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None, silent=False):
    api: StockAPI = context.bot_data['api']
    cleaned = await clear_old_history(api, CONFIG["keep_count"])
    
    if not silent:
        if cleaned > 0:
            await update.message.reply_text(f"🧹 已清理 {cleaned} 条旧记录，历史已从系统中抹去。")
        else:
            await update.message.reply_text("✨ 当前只有 {} 条记录，还不够成为故事。".format(cleaned))
