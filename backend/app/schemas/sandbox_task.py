from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class DispatchTask(BaseModel):
    """Request to dispatch an agent to the Anthropic sandbox."""
    agent_id: str
    task: str


class SandboxTaskOut(BaseModel):
    id: str
    agent_id: str
    managed_agent_id: Optional[str]
    environment_id: Optional[str]
    session_id: Optional[str]
    task: str
    status: str
    result: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SandboxTaskEvents(BaseModel):
    session_id: str
    status: str
    events: List[dict]
