"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Description: 股票分析命令处理函数
"""

import os

from telegram import Update
from telegram.ext import ContextTypes

from src.stock_bot.bot.commands.basic import cmd_clear
from src.stock_bot.infrastructure.stock_api import StockAPI
from src.stock_bot.utils.chart import generate_candlestick_image
from src.stock_bot.utils.logger import setup_logger

logger = setup_logger('commands.analysis')


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE, parts):
    api: StockAPI = context.bot_data['api']
    stock_code = parts[1]
    data = await api.get_quote(stock_code)
    if data:
        cp = float(data.get('change_percent', 0))
        icon = '🔴' if cp > 0 else '🟢' if cp < 0 else '⚪'
        text = (
            f'{icon} **{data.get("stock_name")} ({data.get("stock_code")})**\n'
            f'━━━━━━━━━━━━━\n'
            f'💰 **现价：{data.get("current_price")}** ({cp}%)\n'
            f'🌅 开盘：{data.get("open")}  高：{data.get("high")}  低：{data.get("low")}\n'
            f'📊 成交量：{int(data.get("volume", 0)):,}'
        )
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text('❌ 行情数据暂时‘罢工’，系统翻遍了也没找到可用结果。')


async def handle_kline(update: Update, context: ContextTypes.DEFAULT_TYPE, parts):
    api: StockAPI = context.bot_data['api']
    stock_code = parts[1]
    status_msg = await update.message.reply_text(f'🚀 正在抓取 {stock_code} 的K线数据…主力也在盯盘中... 快要画冒烟了')
    k_data = await api.get_kline_plot_data(stock_code, 120)
    img_path = generate_candlestick_image(stock_code, k_data, 60)

    if img_path and os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=f,
                caption=f'📈 {stock_code} K线图 (仅供参考)',
                reply_to_message_id=update.message.message_id,
            )
        await status_msg.delete()
        os.remove(img_path)
    else:
        await status_msg.edit_text(f'💥 {stock_code} K 线图没画出来，可能行情自己都看不懂。')


async def handle_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, parts):
    api: StockAPI = context.bot_data['api']
    code, name = parts[0], ' '.join(parts[1:])
    status_msg = await update.message.reply_text(f'🚀 正在对 {name} 正在评估你是价值投资还是情绪选手')
    try:
        resp = await api.analyze(code, name)
        if resp.status_code in [200, 202]:
            await cmd_clear(update, context, silent=True)
            await status_msg.edit_text(f'✅ **{name}** 已提交分析，请耐心等待市场教育结果。别催，再催就自我毁灭了哦！')
        else:
            await status_msg.edit_text(f'❌ 接口翻车了 (状态码: {resp.status_code})，这波不怪你。')
    except Exception as e:
        await status_msg.edit_text(f'❌ 提交异常: {e}')
