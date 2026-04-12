from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from app.database import Base


class CredentialEntry(Base):
    """Secure credential tracker — stores references to logins and API keys.
    NOTE: This is an INDEX/TRACKER, not a password manager.
    Store actual passwords in a real password manager (1Password, Bitwarden, etc.)
    This tracks WHAT credentials exist and WHERE they're stored.
    """
    __tablename__ = "credential_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    service = Column(String, nullable=False)  # "YouTube", "Instagram", "Make.com", "Anthropic", "ElevenLabs"
    account_name = Column(String, nullable=False)  # Username/email
    category = Column(String, default="social")  # social, api, tool, hosting, email, other
    platform_url = Column(String, default="")  # Login URL
    notes = Column(Text, default="")  # "Stored in 1Password" or "Ask Pedro"
    api_key_hint = Column(String, default="")  # Last 4 chars only, e.g. "...MQAA"
    managed_by = Column(String, default="")  # Which agent uses this
    status = Column(String, default="active")  # active, expired, rotating, pending
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    extra_data = Column(JSON, default=dict)
