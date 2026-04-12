import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, JSON
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(String, nullable=True)  # agent id
    due_date = Column(String, nullable=True)
    priority = Column(String, default="P2")  # P0, P1, P2, P3
    status = Column(String, default="queued")  # queued, in_progress, in_review, blocked, complete
    project = Column(String, nullable=True)
    created_by_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    description = Column(Text, nullable=True)
    due_date = Column(String, nullable=True)
    status = Column(String, default="draft")  # draft, sent, paid, overdue, cancelled
    created_by_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
