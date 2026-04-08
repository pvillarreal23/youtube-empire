"""
YouTube Empire — Telegram Bot

Commands:
  /pipeline <topic>    — Run full content pipeline
  /agent <agent> <msg> — Message a specific agent
  /autopilot           — Run autopilot (trend research → full pipeline)
  /agents              — List all available agents
  /status <id>         — Check pipeline status

Setup:
  1. Message @BotFather on Telegram
  2. Send /newbot and follow the steps
  3. Copy the bot token
  4. Set TELEGRAM_BOT_TOKEN in your .env
  5. Run: python -m bots.telegram_bot
"""

import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_URL = os.getenv("API_URL", "http://localhost:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


async def api_call(method: str, path: str, json_data: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=300) as http:
        if method == "GET":
            resp = await http.get(f"{API_URL}{path}")
        else:
            resp = await http.post(f"{API_URL}{path}", json=json_data)
        resp.raise_for_status()
        return resp.json()


def truncate(text: str, limit: int = 4000) -> str:
    """Telegram has a 4096 char limit per message."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...(truncated)"


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "YouTube Empire Bot\n\n"
        "Commands:\n"
        "/pipeline <topic> — Full content pipeline\n"
        "/autopilot — Auto find topic & create package\n"
        "/agent <id> <message> — Message an agent\n"
        "/agents — List all agents\n"
        "/status <id> — Check pipeline status"
    )


async def pipeline_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /pipeline <topic>\nExample: /pipeline AI replacing freelancers in 2026")
        return

    topic = " ".join(context.args)
    await update.message.reply_text(f"Starting pipeline for: *{topic}*\nThis may take a few minutes...", parse_mode="Markdown")

    try:
        result = await api_call("POST", "/api/webhooks/trigger", {
            "action": "run_pipeline",
            "topic": topic,
        })
        thread_id = result["thread_id"]
        await update.message.reply_text(f"Pipeline running. ID: `{thread_id}`", parse_mode="Markdown")

        # Poll until complete
        for _ in range(60):
            await asyncio.sleep(10)
            status = await api_call("GET", f"/api/webhooks/pipeline/{thread_id}")

            if status["status"] == "complete":
                results = status.get("results", {})
                for agent_id, content in results.items():
                    await update.message.reply_text(
                        f"*{agent_id}*\n\n{truncate(content)}",
                        parse_mode="Markdown",
                    )
                await update.message.reply_text("Pipeline complete.")
                return

            if status["status"] == "failed":
                await update.message.reply_text("Pipeline failed.")
                return

        await update.message.reply_text("Pipeline timed out. Use /status to check.")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:500]}")


async def autopilot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Starting autopilot...\n"
        "Trend Researcher → Content VP → Full Pipeline.\n"
        "This takes several minutes."
    )

    try:
        await api_call("POST", "/api/pipeline/autopilot", {
            "channel": "V-Real AI",
            "niche": "AI agents, automation, and building income with AI",
            "num_ideas": 3,
        })
        await update.message.reply_text("Autopilot started. You'll see results come in shortly.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:500]}")


async def agent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /agent <agent-id> <message>\n"
            "Example: /agent scriptwriter-agent Write a hook about AI tools"
        )
        return

    agent_id = context.args[0]
    message = " ".join(context.args[1:])
    await update.message.reply_text(f"Sending to *{agent_id}*...", parse_mode="Markdown")

    try:
        result = await api_call("POST", "/api/webhooks/trigger", {
            "action": "run_agent",
            "agent_ids": [agent_id],
            "content": message,
        })
        thread_id = result["thread_id"]

        for _ in range(30):
            await asyncio.sleep(5)
            status = await api_call("GET", f"/api/webhooks/pipeline/{thread_id}")
            results = status.get("results", {})
            if agent_id in results:
                await update.message.reply_text(truncate(results[agent_id]))
                return

        await update.message.reply_text("Agent still thinking. Check /status later.")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:500]}")


async def agents_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        agents = await api_call("GET", "/api/webhooks/agents")
        by_dept: dict[str, list] = {}
        for a in agents:
            dept = a["department"]
            if dept not in by_dept:
                by_dept[dept] = []
            by_dept[dept].append(a)

        lines = []
        for dept, dept_agents in sorted(by_dept.items()):
            lines.append(f"\n*{dept.upper()}*")
            for a in dept_agents:
                lines.append(f"  `{a['id']}` — {a['name']}")

        msg = "*Available Agents:*\n" + "\n".join(lines)
        await update.message.reply_text(truncate(msg), parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:500]}")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /status <pipeline-id>")
        return

    pipeline_id = context.args[0]
    try:
        status = await api_call("GET", f"/api/webhooks/pipeline/{pipeline_id}")
        completed = ", ".join(status.get("completed_agents", [])) or "None yet"
        pending = ", ".join(status.get("pending_agents", [])) or "None"

        await update.message.reply_text(
            f"*Status:* {status['status']}\n"
            f"*Completed:* {completed}\n"
            f"*Pending:* {pending}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:500]}")


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN in .env")
        sys.exit(1)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("pipeline", pipeline_cmd))
    app.add_handler(CommandHandler("autopilot", autopilot_cmd))
    app.add_handler(CommandHandler("agent", agent_cmd))
    app.add_handler(CommandHandler("agents", agents_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    print("Telegram bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
