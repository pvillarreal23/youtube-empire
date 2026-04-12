import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-key-here":
    print("WARNING: ANTHROPIC_API_KEY not set — agent responses will fail. Add it to .env")

DATABASE_URL = "sqlite+aiosqlite:///./data/empire.db"
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "agents" / "vreal-ai"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://192.168.183.114:3000").split(",")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_ROUTER_MODEL = os.getenv("CLAUDE_ROUTER_MODEL", "claude-haiku-4-5-20251001")
MAX_ROUTING_HOPS = 5
MAX_AGENTS_PER_TURN = 3
