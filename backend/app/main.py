from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, async_session
from app.services.agent_loader import load_agents_to_db
from app.tools.loader import sync_tools_to_db
import app.models  # noqa: F401 — register all models with Base
import os

# Import tool modules to trigger @tool decorator registration
import app.tools.business_ops  # noqa: F401
import app.tools.project_mgmt  # noqa: F401
import app.tools.data_analytics  # noqa: F401
import app.tools.communication  # noqa: F401
import app.tools.memory  # noqa: F401

os.makedirs("data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB, load agents, sync tools
    await init_db()
    async with async_session() as session:
        await load_agents_to_db(session)
        await sync_tools_to_db(session)
    print("Loaded agents and tools into database")
    yield


app = FastAPI(title="YouTube Empire", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import agents, threads, tools, tasks  # noqa: E402

app.include_router(agents.router)
app.include_router(threads.router)
app.include_router(tools.router)
app.include_router(tasks.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
