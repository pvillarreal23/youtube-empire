import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, nullable=False)
    channel = Column(String, nullable=True)  # ai-tech, finance, psychology, or None (all)
    status = Column(String, default="running")  # running, completed, failed
    session_id = Column(String, nullable=True)  # Managed Agent session ID
    output = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
