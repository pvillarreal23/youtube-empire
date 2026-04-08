import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
DATABASE_URL = "sqlite+aiosqlite:///./data/empire.db"
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_ROUTER_MODEL = "claude-haiku-4-5-20251001"
MAX_ROUTING_HOPS = 5
MAX_AGENTS_PER_TURN = 3
