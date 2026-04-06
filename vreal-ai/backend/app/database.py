from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    # Import all models so they register with Base.metadata
    from app.models import agent, thread, scheduler, production, feed, workspace, social, vault, tools, skills  # noqa: F401
    from app.services import agent_memory  # noqa: F401 — registers memory tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
