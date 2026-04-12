from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, async_session
from app.services.agent_loader import load_agents_to_db
from app.services.scheduler import init_scheduled_tasks, start_scheduler, stop_scheduler
from app.routers import agents, threads
from app.routers.scheduler import router as scheduler_router
from app.routers.production import router as production_router
from app.routers.feed import router as feed_router
from app.routers.collab import router as collab_router
from app.routers.workspace import router as workspace_router
from app.routers.social import router as social_router
from app.routers.vault import router as vault_router
from app.routers.tools import router as tools_router, init_tools
from app.routers.media import router as media_router
from app.routers.skills import router as skills_router
from app.services.skill_seeder import seed_baseline_skills
from app.config import CORS_ORIGINS
import os

os.makedirs("data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB, load agents, init scheduler
    await init_db()
    async with async_session() as session:
        await load_agents_to_db(session)
    print("Loaded agents into database")
    new_skills = await seed_baseline_skills()
    if new_skills:
        print(f"Seeded {new_skills} baseline skills across all agents")
    else:
        print("Agent skills already seeded — ready to grow")
    await init_scheduled_tasks()
    await init_tools()
    await start_scheduler()
    print("Scheduler initialized — agents are running autonomously on cron")
    yield
    stop_scheduler()


app = FastAPI(title="YouTube Empire", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(threads.router)
app.include_router(scheduler_router)
app.include_router(production_router)
app.include_router(feed_router)
app.include_router(collab_router)
app.include_router(workspace_router)
app.include_router(social_router)
app.include_router(vault_router)
app.include_router(tools_router)
app.include_router(media_router)
app.include_router(skills_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
