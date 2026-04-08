"""
YouTube Empire — Discord Bot

Commands:
  /pipeline <topic>    — Run full content pipeline
  /agent <agent> <msg> — Message a specific agent
  /autopilot           — Run autopilot (trend research → full pipeline)
  /agents              — List all available agents
  /status <id>         — Check pipeline status

Setup:
  1. Create a bot at https://discord.com/developers/applications
  2. Enable Message Content Intent under Bot settings
  3. Copy the bot token
  4. Set DISCORD_BOT_TOKEN in your .env
  5. Invite bot to your server with the OAuth2 URL (bot + applications.commands scopes)
  6. Run: python -m bots.discord_bot
"""

import os
import sys
import asyncio
from pathlib import Path

import discord
from discord import app_commands

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

import httpx

API_URL = os.getenv("API_URL", "http://localhost:8000")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def api_call(method: str, path: str, json_data: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=300) as http:
        if method == "GET":
            resp = await http.get(f"{API_URL}{path}")
        else:
            resp = await http.post(f"{API_URL}{path}", json=json_data)
        resp.raise_for_status()
        return resp.json()


@tree.command(name="pipeline", description="Run full content pipeline on a topic")
@app_commands.describe(topic="The video topic to create a package for")
async def pipeline_cmd(interaction: discord.Interaction, topic: str):
    await interaction.response.send_message(f"Starting pipeline for: **{topic}**\nThis may take a few minutes...")

    try:
        result = await api_call("POST", "/api/webhooks/trigger", {
            "action": "run_pipeline",
            "topic": topic,
        })
        thread_id = result["thread_id"]

        await interaction.followup.send(
            f"Pipeline running. ID: `{thread_id}`\n"
            f"Use `/status {thread_id}` to check progress."
        )

        # Poll until complete (max 10 minutes)
        for _ in range(60):
            await asyncio.sleep(10)
            status = await api_call("GET", f"/api/webhooks/pipeline/{thread_id}")

            if status["status"] == "complete":
                # Send results split by agent
                results = status.get("results", {})
                for agent_id, content in results.items():
                    # Discord has a 2000 char limit per message
                    header = f"**{agent_id}**\n"
                    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
                    for chunk in chunks:
                        await interaction.followup.send(f"{header}{chunk}")
                        header = ""
                await interaction.followup.send("Pipeline complete.")
                return

            if status["status"] == "failed":
                await interaction.followup.send("Pipeline failed. Check the dashboard for details.")
                return

        await interaction.followup.send("Pipeline timed out. Use `/status` to check manually.")

    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)[:500]}")


@tree.command(name="autopilot", description="Run autopilot — agents find topic and create full package")
async def autopilot_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Starting autopilot...\n"
        "Trend Researcher will find the best topic, Content VP will approve it, "
        "and the full pipeline will run. This takes several minutes."
    )

    try:
        result = await api_call("POST", "/api/pipeline/autopilot", {
            "channel": "V-Real AI",
            "niche": "AI agents, automation, and building income with AI",
            "num_ideas": 3,
        })
        await interaction.followup.send(f"Autopilot started. Check the dashboard for results.")
    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)[:500]}")


@tree.command(name="agent", description="Send a message to a specific agent")
@app_commands.describe(agent_id="Agent ID (e.g. scriptwriter-agent)", message="Your message")
async def agent_cmd(interaction: discord.Interaction, agent_id: str, message: str):
    await interaction.response.send_message(f"Sending to **{agent_id}**...")

    try:
        result = await api_call("POST", "/api/webhooks/trigger", {
            "action": "run_agent",
            "agent_ids": [agent_id],
            "content": message,
        })
        thread_id = result["thread_id"]

        # Wait for response
        for _ in range(30):
            await asyncio.sleep(5)
            status = await api_call("GET", f"/api/webhooks/pipeline/{thread_id}")
            results = status.get("results", {})
            if agent_id in results:
                content = results[agent_id]
                chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
                for chunk in chunks:
                    await interaction.followup.send(chunk)
                return

        await interaction.followup.send("Agent is still thinking. Check back with `/status`.")

    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)[:500]}")


@tree.command(name="agents", description="List all available agents")
async def agents_cmd(interaction: discord.Interaction):
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
            lines.append(f"\n**{dept.upper()}**")
            for a in dept_agents:
                lines.append(f"  `{a['id']}` — {a['name']} ({a['role']})")

        msg = "**Available Agents:**\n" + "\n".join(lines)
        await interaction.response.send_message(msg[:2000])

    except Exception as e:
        await interaction.response.send_message(f"Error: {str(e)[:500]}")


@tree.command(name="status", description="Check pipeline status")
@app_commands.describe(pipeline_id="The pipeline/thread ID")
async def status_cmd(interaction: discord.Interaction, pipeline_id: str):
    try:
        status = await api_call("GET", f"/api/webhooks/pipeline/{pipeline_id}")
        completed = ", ".join(status.get("completed_agents", [])) or "None yet"
        pending = ", ".join(status.get("pending_agents", [])) or "None"

        await interaction.response.send_message(
            f"**Pipeline Status:** {status['status']}\n"
            f"**Completed:** {completed}\n"
            f"**Pending:** {pending}"
        )
    except Exception as e:
        await interaction.response.send_message(f"Error: {str(e)[:500]}")


@client.event
async def on_ready():
    await tree.sync()
    print(f"Discord bot ready: {client.user}")


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("Set DISCORD_BOT_TOKEN in .env")
        sys.exit(1)
    client.run(DISCORD_BOT_TOKEN)
