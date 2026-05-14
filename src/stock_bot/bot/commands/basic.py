"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.
"""

from telegram import Update
from telegram.ext import ContextTypes

from src.stock_bot.utils.logger import setup_logger

logger = setup_logger('commands.basic')

COMMAND_DOCS = {
    'help': '显示帮助菜单',
    'usage': '获取大模型消耗统计[today|month|all]',
    'list': '查看个股历史分析记录',
    'price <代码>': '实时价格行情查询',
    'kline <代码>': '获取个股 K 线图',
    'clear': '清理个股分析历史记录',
    'market_review': '大盘分析任务',
    '<代码> <名称>': '个股深度分析',
}


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    bot_name = context.bot.username or 'StockBot'
    help_text = (
        '🤖 **当前版本还在‘成长中’，暂时只解锁了少量指令技能，其它功能正在路上，别急，它还在加班进化。**\n\n'
        + '\n'.join([f'• `@{bot_name} {k}`: {v}' for k, v in COMMAND_DOCS.items()])
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')
