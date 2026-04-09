import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DATABASE_URL = "sqlite+aiosqlite:///./data/empire.db"
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"

# Model presets — selectable via CLAUDE_MODEL_PRESET env var
MODEL_PRESETS = {
    "sonnet": {
        "id": "claude-sonnet-4-20250514",
        "label": "Claude Sonnet 4",
        "max_tokens": 2048,
        "router_model": "claude-haiku-4-5-20251001",
        "router_max_tokens": 256,
        "extended_thinking": False,
        "context_window": 200_000,
    },
    "opus": {
        "id": "claude-opus-4-6",
        "label": "Claude Opus 4.6",
        "max_tokens": 4096,
        "router_model": "claude-haiku-4-5-20251001",
        "router_max_tokens": 256,
        "extended_thinking": False,
        "context_window": 1_000_000,
    },
    "mythos": {
        "id": "claude-mythos-preview",
        "label": "Claude Mythos Preview",
        "max_tokens": 16384,
        "router_model": "claude-mythos-preview",
        "router_max_tokens": 1024,
        "extended_thinking": True,
        "thinking_budget": 10000,
        "context_window": 1_000_000,
    },
}

ACTIVE_PRESET = os.getenv("CLAUDE_MODEL_PRESET", "mythos")
_preset = MODEL_PRESETS.get(ACTIVE_PRESET, MODEL_PRESETS["mythos"])

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", _preset["id"])
CLAUDE_MODEL_LABEL = _preset["label"]
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", str(_preset["max_tokens"])))
CLAUDE_ROUTER_MODEL = os.getenv("CLAUDE_ROUTER_MODEL", _preset["router_model"])
CLAUDE_ROUTER_MAX_TOKENS = _preset["router_max_tokens"]
CLAUDE_EXTENDED_THINKING = _preset["extended_thinking"]
CLAUDE_THINKING_BUDGET = _preset.get("thinking_budget", 10000)
CLAUDE_CONTEXT_WINDOW = _preset["context_window"]

MAX_ROUTING_HOPS = 5
MAX_AGENTS_PER_TURN = 3
