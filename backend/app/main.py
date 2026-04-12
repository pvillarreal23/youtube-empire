from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, async_session
from app.services.agent_loader import load_agents_to_db
from app.routers import agents, threads
from app.routers import automation
import os

os.makedirs("data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB and load agents
    await init_db()
    async with async_session() as session:
        await load_agents_to_db(session)
    print("Loaded agents into database")

    # Register managed agents for automation workflows
    from app.services.managed_agents import register_agents, ensure_environment
    try:
        await ensure_environment()
        await register_agents()
        print("Registered managed agents for automation")
    except Exception as e:
        print(f"Managed agent registration skipped: {e}")

    yield


app = FastAPI(title="YouTube Empire", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(threads.router)
app.include_router(automation.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/model")
async def model_info():
    """Return the active model configuration."""
    from app.config import (
        CLAUDE_MODEL,
        CLAUDE_MODEL_LABEL,
        CLAUDE_MAX_TOKENS,
        CLAUDE_ROUTER_MODEL,
        CLAUDE_EXTENDED_THINKING,
        CLAUDE_THINKING_BUDGET,
        CLAUDE_CONTEXT_WINDOW,
        ACTIVE_PRESET,
        MODEL_PRESETS,
    )
    return {
        "active_preset": ACTIVE_PRESET,
        "model": CLAUDE_MODEL,
        "label": CLAUDE_MODEL_LABEL,
        "max_tokens": CLAUDE_MAX_TOKENS,
        "router_model": CLAUDE_ROUTER_MODEL,
        "extended_thinking": CLAUDE_EXTENDED_THINKING,
        "thinking_budget": CLAUDE_THINKING_BUDGET if CLAUDE_EXTENDED_THINKING else None,
        "context_window": CLAUDE_CONTEXT_WINDOW,
        "available_presets": list(MODEL_PRESETS.keys()),
    }
