import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.database import Base


class Thread(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status = Column(String, default="active")  # active, resolved, archived
    participants = Column(JSON, default=list)  # list of agent ids


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, nullable=False)
    sender_type = Column(String, nullable=False)  # "user" or "agent"
    sender_agent_id = Column(String, nullable=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="sent")  # sent, processing, complete, failed
    message_type = Column(String, default="text")  # text, tool_result
    tool_calls = Column(JSON, nullable=True)  # list of ToolCall IDs
