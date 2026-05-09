"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Description: 管理员命令处理函数
"""

import subprocess
from telegram import Update
from telegram.ext import ContextTypes
from src.stock_bot.config.settings import CONFIG
from src.stock_bot.utils.logger import setup_logger
from src.stock_bot.infrastructure.stock_api import StockAPI

logger = setup_logger("commands.admin")


async def cmd_usage(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    api: "StockAPI" = context.bot_data.get('api')
    if not api:
        return await update.message.reply_text("❌ 系统还没准备好，像极了开盘前的你。")
    logger.info("cmd_usage 被调用")
    await api.login_if_needed()
    try:
        r = await api.client.get("/api/v1/usage/summary", params={"period": "today"})
        if r.status_code != 200:
            return await update.message.reply_text(f"❌ 获取统计失败：服务器返回了错误状态码 `{r.status_code}`。")
        d = r.json()
        report_date = d.get("from_date", "今日")
        msg = f"📊 **大模型用量统计 ({report_date})**\n━━━━━━━━━━━━━━━\n"
        msg += f"总调用: `{d.get('total_calls', 0)}` 次\n总消耗: `{d.get('total_tokens', 0):,}` Tokens\n\n"
        if d.get("by_model"):
            msg += "🤖 **模型分布**\n"
            for item in d.get("by_model", []):
                model_short_name = item.get('model', 'Unknown').split('/')[-1]
                msg += f"• {model_short_name}: {item.get('calls', 0)} 次 (`{item.get('total_tokens', 0):,}` tokens)\n"
        else:
            msg += "_今日暂无详细模型消耗记录_"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"cmd_usage 异常: {e}")
        await update.message.reply_text(f"💥 系统异常：原因: `{str(e)}`")


async def cmd_market_review(update: Update, context: ContextTypes.DEFAULT_TYPE, args=None):
    user_id = str(update.message.from_user.id)
    logger.info(f"market_review 命令被调用 | 用户ID: {user_id}")

    if CONFIG.get("admin_ids") and user_id not in CONFIG.get("admin_ids", []):
        logger.warning(f"非管理员尝试执行 market_review | 用户ID: {user_id}")
        return await update.message.reply_text(f"🚫 抱歉，你没有管理员权限。(ID: {user_id})")

    logger.info("权限校验通过，开始执行大盘复盘任务")
    status_msg = await update.message.reply_text("🐳 正在启动(缅A)大盘复盘任务，看看今天是谁在收割情绪")
    docker_cmd = ["docker", "exec", "stock-server", "python", "main.py", "--market-review"]
    logger.info(f"执行 Docker 命令: {' '.join(docker_cmd)}")
    try:
        process = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info("Docker 进程已启动，等待执行结果...")

        try:
            stdout, stderr = process.communicate(timeout=600)
            if stdout:
                for line in stdout.splitlines():
                    if line.strip():
                        logger.info(line.strip())
            if process.returncode == 0:
                logger.info("大盘复盘任务执行成功")
                await status_msg.edit_text("✅ **复盘任务已完成！**\n\n终端输出：\n`{}`".format(stdout[-500:]), parse_mode="Markdown")
            else:
                logger.error(f"任务执行失败，返回码: {process.returncode}")
                await status_msg.edit_text(f"❌ 任务出错：\n`{stderr}`", parse_mode="Markdown")
        except subprocess.TimeoutExpired:
            logger.warning("大盘复盘任务执行超时")
            await status_msg.edit_text("⏳ 任务还在跑，市场也还在演，你可以晚点再来看结果")
    except Exception as e:
        logger.error(f"执行 market_review 异常: {e}", exc_info=True)
        await status_msg.edit_text(f"💥 调度失败: {str(e)}")
