import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, JSON, DateTime
from app.database import Base


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    memory_type = Column(String, nullable=False)  # fact, decision, task_result, preference
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    source_thread_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
