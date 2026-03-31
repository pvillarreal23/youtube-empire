from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, async_session
from app.services.agent_loader import load_agents_to_db
from app.routers import agents, threads
import os

os.makedirs("data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB and load agents
    await init_db()
    async with async_session() as session:
        await load_agents_to_db(session)
    print("Loaded agents into database")
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
