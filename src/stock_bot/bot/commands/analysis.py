"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.
"""

import httpx
from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import ContextTypes

from src.stock_bot.infrastructure.stock_api import StockAPI
from src.stock_bot.utils.logger import setup_logger

logger = setup_logger('commands.analysis')


async def handle_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, parts):
    api: StockAPI = context.bot_data['api']
    code, name = parts[0], ' '.join(parts[1:])
    status_msg = await update.message.reply_text(f'🚀 正在对 {name} 进行分析, 同时评估你是价值投资还是情绪选手')
    try:
        resp = await api.analyze(code, name)

        if resp.status_code in [200, 202]:
            await status_msg.edit_text(f'✅ **{name}** 已提交分析，请耐心等待市场教育结果。别催，再催就自我毁灭了哦！')
        else:
            await status_msg.edit_text(f'❌ 接口翻车了 (状态码: {resp.status_code})，这波不怪你。')

    except (TimedOut, TimeoutError, httpx.ReadTimeout, httpx.TimeoutException):
        logger.warning(f'分析请求超时: {code} - {name}')
        await status_msg.edit_text(f'⏳ **{name}** 分析任务已经提交，后台仍在处理中，请稍后再查看结果。')

    except NetworkError as e:
        logger.error(f'分析请求网络异常: {code} - {name} - {e}')
        await status_msg.edit_text(f'🌐 网络异常: {e}')

    except Exception as e:
        logger.exception(f'分析请求失败: {code} - {name}')
        await status_msg.edit_text(f'❌ 提交异常: {e}')


async def cmd_market_review(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    logger.info('market_review 命令被调用')

    api: StockAPI = context.bot_data.get('api')
    if not api:
        return await update.message.reply_text('❌ 系统还没准备好，像极了开盘前的你。')

    status_msg = await update.message.reply_text('🚀 正在启动(缅A)大盘复盘任务，看看今天是谁在收割情绪...')

    try:
        # 调用 API 触发任务
        result = await api.trigger_market_review(send_notification=True)

        if result['success']:
            data = result['data']
            task_id = data.get('task_id', 'unknown')

            logger.info(f'大盘复盘任务提交成功 | task_id: {task_id}')

            await status_msg.edit_text(
                f'✅ **大盘复盘任务已成功提交**\n\n'
                f'**任务ID**: `{task_id}`\n'
                f'**状态**: {data.get("status", "accepted")}\n'
                f'**通知**: {"已开启" if data.get("send_notification") else "关闭"}\n\n'
                '任务将在后台异步执行，你可以稍后通过 `/tasks` 查看进度。',
                parse_mode='Markdown',
            )
        else:
            logger.error(f'API 调用失败: {result.get("error")}')
            await status_msg.edit_text(
                f'❌ 提交任务失败\n\n状态码: `{result.get("status_code")}`\n错误信息: `{result.get("error")[:500]}`',
                parse_mode='Markdown',
            )

    except Exception as e:
        logger.error(f'触发 market_review 异常: {e}', exc_info=True)
        await status_msg.edit_text(f'💥 提交任务时发生异常：{e!s}', parse_mode='Markdown')
