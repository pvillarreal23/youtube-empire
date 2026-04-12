import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base


class SandboxTask(Base):
    __tablename__ = "sandbox_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)  # local agent id (e.g. "trend-researcher-agent")
    managed_agent_id = Column(String, nullable=True)  # Anthropic platform agent id
    environment_id = Column(String, nullable=True)  # Anthropic platform environment id
    session_id = Column(String, nullable=True)  # Anthropic platform session id
    task = Column(Text, nullable=False)  # the task / prompt sent to the sandbox
    status = Column(String, default="pending")  # pending, running, completed, failed
    result = Column(Text, nullable=True)  # collected output from the session
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
