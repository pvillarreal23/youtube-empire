import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, JSON, Boolean, DateTime
from app.database import Base


class ToolDefinition(Base):
    __tablename__ = "tool_definitions"

    id = Column(String, primary_key=True)  # e.g. "create-task"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # business_ops, data_analytics, communication, project_mgmt
    input_schema = Column(JSON, nullable=False)  # JSON Schema for Claude tool_use
    handler_module = Column(String, nullable=False)  # dotted path to handler
    requires_approval = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, nullable=True)  # FK to messages.id
    thread_id = Column(String, nullable=True)
    agent_id = Column(String, nullable=False)
    tool_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending, executing, completed, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentToolPermission(Base):
    __tablename__ = "agent_tool_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    tool_id = Column(String, nullable=False)
