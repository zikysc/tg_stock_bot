"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Dispatcher: 负责解析用户消息并分发到对应的命令处理函数
"""

import re

from telegram import Update
from telegram.ext import ContextTypes

from src.stock_bot.infrastructure.stock_api import StockAPI
from src.stock_bot.utils.logger import setup_logger

from .commands.analysis import cmd_market_review, handle_analysis
from .commands.basic import cmd_help
from .commands.history import cmd_clear, cmd_list
from .commands.stocks import handle_kline, handle_price
from .commands.usages import cmd_usage

logger = setup_logger('dispatcher')


async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user = msg.from_user
    logger.info(f'收到消息 | 用户: {user.id} ({user.username}) | 内容: {msg.text[:100]}')

    bot_name = context.bot.username
    api: StockAPI = context.bot_data.get('api')
    if not api:
        return await msg.reply_text('❌ Bot 尚未初始化')

    clean_text = re.sub(rf'^@{re.escape(bot_name)}', '', msg.text).strip()
    parts = clean_text.split()

    if not parts:
        return await msg.reply_text('🤖 已上线，但情绪不太稳定…\n请输入指令，或者 @bot help')

    cmd_key = parts[0].lower()

    # 基础命令
    if cmd_key == 'help':
        return await cmd_help(update, context)
    if cmd_key == 'list':
        return await cmd_list(update, context)
    if cmd_key == 'clear':
        return await cmd_clear(update, context)

    # 需要 API 可达性的检测
    # 先检查一次 API 状态，避免在每个分支里重复等待
    is_api_ready = await api.is_reachable()

    if cmd_key == 'usage':
        if not is_api_ready:
            return await msg.reply_text('🚫 对方不想说话并向你扔了一个 404，行情数据暂时断了。')
        # 传递参数：parts[1:] 包含命令后面的所有参数
        return await cmd_usage(update, context, args=parts[1:])

    if cmd_key == 'market_review':
        if not is_api_ready:
            return await msg.reply_text('🚫 盘后回顾暂不可用，行情连接中断。')
        return await cmd_market_review(update, context)

    # 业务命令处理
    if cmd_key == 'price' and len(parts) >= 2:
        if not is_api_ready:
            return await msg.reply_text('🚫 对方不想说话并向你扔了一个 404，行情数据暂时断了。')
        return await handle_price(update, context, parts)

    if cmd_key == 'kline' and len(parts) >= 2:
        if not is_api_ready:
            return await msg.reply_text('🚫 接口翻车了，主力可能把网线拔了，K线图画不出来。')
        return await handle_kline(update, context, parts)

    # 默认个股分析
    if len(parts) >= 2 and cmd_key not in ['help', 'clear', 'usage', 'price', 'kline', 'market_review']:
        if not await api.is_reachable():
            return await msg.reply_text('🚫 分析任务启动失败，网关那边似乎没什么反应，你可以晚点再来看结果。')
        return await handle_analysis(update, context, parts)

    await msg.reply_text(
        f'❌ 看不懂这个指令: `{cmd_key}`，你在考验我还是市场？执行 `@{bot_name} help` 看看我都能干啥吧！'
    )
