"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Description: 管理员命令处理函数
"""

import subprocess

from telegram import Update
from telegram.ext import ContextTypes

from src.stock_bot.config.settings import CONFIG
from src.stock_bot.infrastructure.stock_api import StockAPI
from src.stock_bot.utils.logger import setup_logger

logger = setup_logger('commands.admin')


async def cmd_usage(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    """
    获取 LLM 使用统计
    用法: usage [today|month|all]
    默认: today
    """
    api: StockAPI = context.bot_data.get('api')
    if not api:
        return await update.message.reply_text('❌ 系统还没准备好，像极了开盘前的你。')

    # 解析参数，默认为 today
    period = 'today'
    if args and len(args) > 0:
        period_input = args[0].lower()
        if period_input in ['today', 'month', 'all']:
            period = period_input
        else:
            return await update.message.reply_text(
                '❌ 参数错误\n\n'
                '**用法**: `usage [today|month|all]`\n'
                '• `today` - 今日统计\n'
                '• `month` - 本月统计\n'
                '• `all` - 全部统计',
                parse_mode='Markdown',
            )

    logger.info(f'cmd_usage 被调用 | 请求 period: {period}')
    await api.login_if_needed()

    try:
        r = await api.client.get('/api/v1/usage/summary', params={'period': period})
        if r.status_code != 200:
            return await update.message.reply_text(f'❌ 获取统计失败：服务器返回了错误状态码 `{r.status_code}`。')

        d = r.json()

        # 从返回数据中获取实际的 period（而不是用请求参数）
        actual_period = d.get('period', period)
        logger.info(f'返回数据 period: {actual_period}')

        # 根据实际返回的 period 生成标题
        period_titles = {
            'today': '📊 **今日大模型用量统计**',
            'month': '📊 **本月大模型用量统计**',
            'all': '📊 **全部大模型用量统计**',
        }

        # 构建时间范围文本
        from_date = d.get('from_date', '')
        to_date = d.get('to_date', '')
        date_range = f'({from_date})' if from_date == to_date else f'({from_date} ~ {to_date})'

        # 构建消息
        msg = f'{period_titles.get(actual_period, "📊 **大模型用量统计**")} {date_range}\n'
        msg += '━━━━━━━━━━━━━━━\n\n'

        # 总体统计
        total_calls = d.get('total_calls', 0)
        total_tokens = d.get('total_tokens', 0)
        msg += '🎯 **总体统计**\n'
        msg += f'• 总调用次数: `{total_calls:,}` 次\n'
        msg += f'• 总消耗 Tokens: `{total_tokens:,}`\n'
        if total_calls > 0:
            avg_tokens = total_tokens / total_calls
            msg += f'• 平均每次调用: `{avg_tokens:,.0f}` tokens\n'
        msg += '\n'

        # 按调用类型分布
        by_call_type = d.get('by_call_type', [])
        if by_call_type:
            msg += '📋 **调用类型分布**\n'
            for item in by_call_type:
                call_type = item.get('call_type', 'Unknown')
                calls = item.get('calls', 0)
                tokens = item.get('total_tokens', 0)
                percentage = (calls / total_calls * 100) if total_calls > 0 else 0

                # 调用类型的友好名称
                type_names = {'analysis': '📈 分析', 'agent': '🤖 智能体', 'market_review': '📊 大盘复盘'}
                type_display = type_names.get(call_type, call_type)

                msg += f'• {type_display}: {calls} 次 ({percentage:.1f}%) | `{tokens:,}` tokens\n'
            msg += '\n'

        # 按模型分布
        by_model = d.get('by_model', [])
        if by_model:
            msg += '🤖 **模型分布**\n'
            for item in by_model:
                model = item.get('model', 'Unknown')
                # 提取模型短名称（取最后一部分）
                model_short = model.split('/')[-1] if '/' in model else model
                calls = item.get('calls', 0)
                tokens = item.get('total_tokens', 0)
                percentage = (calls / total_calls * 100) if total_calls > 0 else 0

                msg += f'• `{model_short}`\n'
                msg += f'  └ {calls} 次 ({percentage:.1f}%) | `{tokens:,}` tokens\n'
        else:
            msg += '_暂无详细模型消耗记录_\n'

        # 添加footer提示
        msg += '\n━━━━━━━━━━━━━━━\n'
        msg += '💡 提示: 使用 `usage [today|month|all]` 查看不同时间范围的统计'

        await update.message.reply_text(msg, parse_mode='Markdown')
        logger.info(f'cmd_usage 执行成功 | 请求: {period}, 实际: {actual_period}')

    except Exception as e:
        logger.error(f'cmd_usage 异常: {e}', exc_info=True)
        await update.message.reply_text(f'💥 系统异常：`{e!s}`', parse_mode='Markdown')


async def cmd_market_review(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    user_id = str(update.message.from_user.id)
    logger.info(f'market_review 命令被调用 | 用户ID: {user_id}')

    if CONFIG.get('admin_ids') and user_id not in CONFIG.get('admin_ids', []):
        logger.warning(f'非管理员尝试执行 market_review | 用户ID: {user_id}')
        return await update.message.reply_text(f'🚫 抱歉，你没有管理员权限。(ID: {user_id})')

    logger.info('权限校验通过，开始执行大盘复盘任务')
    status_msg = await update.message.reply_text('🐳 正在启动(缅A)大盘复盘任务，看看今天是谁在收割情绪')
    docker_cmd = ['docker', 'exec', 'stock-server', 'python', 'main.py', '--market-review']
    logger.info(f'执行 Docker 命令: {" ".join(docker_cmd)}')
    try:
        process = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info('Docker 进程已启动，等待执行结果...')

        try:
            stdout, stderr = process.communicate(timeout=600)
            if stdout:
                for line in stdout.splitlines():
                    if line.strip():
                        logger.info(line.strip())
            if process.returncode == 0:
                logger.info('大盘复盘任务执行成功')
                await status_msg.edit_text(
                    f'✅ **复盘任务已完成！**\n\n终端输出：\n`{stdout[-500:]}`', parse_mode='Markdown'
                )
            else:
                logger.error(f'任务执行失败，返回码: {process.returncode}')
                await status_msg.edit_text(f'❌ 任务出错：\n`{stderr}`', parse_mode='Markdown')
        except subprocess.TimeoutExpired:
            logger.warning('大盘复盘任务执行超时')
            await status_msg.edit_text('⏳ 任务还在跑，市场也还在演，你可以晚点再来看结果')
    except Exception as e:
        logger.error(f'执行 market_review 异常: {e}', exc_info=True)
        await status_msg.edit_text(f'💥 调度失败: {e!s}')
