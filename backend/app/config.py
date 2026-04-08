import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
KLING_API_KEY = os.getenv("KLING_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
CREATOMATE_API_KEY = os.getenv("CREATOMATE_API_KEY", "")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")
NOTIFICATION_WEBHOOK_URL = os.getenv("NOTIFICATION_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DATABASE_URL = "sqlite+aiosqlite:///./data/empire.db"
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_ROUTER_MODEL = "claude-haiku-4-5-20251001"
MAX_ROUTING_HOPS = 5
MAX_AGENTS_PER_TURN = 3
