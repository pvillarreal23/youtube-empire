import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DATABASE_URL = "sqlite+aiosqlite:///./data/empire.db"
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_ROUTER_MODEL = "claude-haiku-4-5-20251001"
MAX_ROUTING_HOPS = 5
MAX_AGENTS_PER_TURN = 3

# AI Media Generation
FAL_API_KEY = os.getenv("FAL_API_KEY", "")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")

# Video Assembly
OUTPUT_DIR = Path("output")
MEDIA_OUTPUT_DIR = OUTPUT_DIR / "media"
ASSEMBLED_OUTPUT_DIR = OUTPUT_DIR / "assembled"
TEMP_DIR = OUTPUT_DIR / "temp"

# Ensure output directories exist
for d in [OUTPUT_DIR, MEDIA_OUTPUT_DIR, ASSEMBLED_OUTPUT_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)
