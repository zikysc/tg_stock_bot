"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Dispatcher: 启动 Telegram Bot, 并开始轮询消息。
"""

import asyncio

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from src.stock_bot.bot.commands.basic import cmd_help
from src.stock_bot.bot.dispatcher import handle_mention
from src.stock_bot.config.settings import BASE_URL, STOCK_PASSWORD, TELEGRAM_TOKEN
from src.stock_bot.infrastructure.stock_api import StockAPI
from src.stock_bot.utils.logger import setup_logger

# 初始化日志
logger = setup_logger('stock_bot')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """全局错误处理器"""
    error = context.error
    logger.error(f'❌ Telegram Bot 异常: {error}', exc_info=True)

    # 尝试通知用户
    if update and hasattr(update, 'message') and update.message:
        try:
            await update.message.reply_text(
                '⚠️ 系统出现异常，已自动记录日志。\n请稍后重试或联系管理员。', parse_mode='Markdown'
            )
        except Exception:
            pass  # 防止错误处理器本身崩溃


def main():
    if not TELEGRAM_TOKEN:
        logger.critical('❌ TELEGRAM_BOT_TOKEN 未在 .env 中配置！')
        print('❌ 请检查 .env 文件中的 TELEGRAM_BOT_TOKEN')
        return

    logger.info('🚀 正在启动 Stock Telegram Bot...')

    api_client = StockAPI(BASE_URL, STOCK_PASSWORD)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.bot_data['api'] = api_client

    # 注册消息处理器
    app.add_handler(
        MessageHandler(filters.TEXT & (filters.Entity('mention') | filters.CaptionEntity('mention')), handle_mention)
    )
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT, handle_mention))
    app.add_handler(CommandHandler('help', cmd_help))

    # 注册全局错误处理器
    app.add_error_handler(error_handler)

    logger.info('✅ Bot 启动成功，正在轮询消息... 按 Ctrl+C 停止')

    try:
        app.run_polling(close_loop=False)
    except KeyboardInterrupt:
        logger.info('🛑 Bot 已手动停止')
    except Exception as e:
        logger.critical(f'💥 Bot 意外停止: {e}', exc_info=True)
    finally:
        logger.info('📴 Bot 已关闭')


if __name__ == '__main__':
    try:
        asyncio.run(main()) if hasattr(asyncio, 'run') else main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f'启动失败: {e}', exc_info=True)
