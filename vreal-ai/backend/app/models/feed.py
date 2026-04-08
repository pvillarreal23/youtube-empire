from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean
from app.database import Base


class FeedMessage(Base):
    """Live feed messages from agents — like a company Slack channel."""
    __tablename__ = "feed_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    channel = Column(String, default="general")  # general, content, operations, analytics, monetization, alerts, wins
    content = Column(Text, nullable=False)
    message_type = Column(String, default="update")  # update, alert, win, request, report, milestone
    severity = Column(String, default="info")  # info, warning, urgent, celebration
    thread_id = Column(String, nullable=True)  # Link to full conversation if applicable
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read = Column(Boolean, default=False)


# Feed channels
FEED_CHANNELS = {
    "general": {"name": "General", "emoji": "💬", "desc": "Company-wide updates"},
    "content": {"name": "Content", "emoji": "📝", "desc": "Scripts, topics, publishing updates"},
    "operations": {"name": "Operations", "emoji": "⚙️", "desc": "Pipeline, production, QA"},
    "analytics": {"name": "Analytics", "emoji": "📊", "desc": "Metrics, trends, performance"},
    "monetization": {"name": "Revenue", "emoji": "💰", "desc": "Deals, affiliates, products"},
    "alerts": {"name": "Alerts", "emoji": "🚨", "desc": "Urgent items needing attention"},
    "wins": {"name": "Wins", "emoji": "🏆", "desc": "Milestones, achievements, celebrations"},
}
