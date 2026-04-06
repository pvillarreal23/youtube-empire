from sqlalchemy import Column, String, Text, JSON
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)  # e.g. "ceo-agent"
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    reports_to = Column(String, nullable=True)  # agent id or None
    direct_reports = Column(JSON, default=list)
    collaborates_with = Column(JSON, default=list)
    file_path = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    avatar_color = Column(String, default="#6366f1")
    department = Column(String, default="general")
