from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from app.database import Base


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    prompt = Column(Text, nullable=False)
    cron_expression = Column(String, nullable=False)  # e.g. "0 9 * * 1" = Mon 9am
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    category = Column(String, default="general")  # content, operations, analytics, etc.


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scheduled_task_id = Column(String, nullable=False)
    thread_id = Column(String, nullable=True)
    agent_id = Column(String, nullable=False)
    task_name = Column(String, default="")
    status = Column(String, default="running")  # running, complete, failed, escalated
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)  # Brief summary of what the agent did


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(String, default="medium")  # low, medium, high, critical
    status = Column(String, default="pending")  # pending, reviewed, resolved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(Text, nullable=True)
