from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class WorkflowInfo(BaseModel):
    id: str
    name: str
    description: str
    agents_used: List[str]
    channel_specific: bool


class RunWorkflowRequest(BaseModel):
    channel: Optional[str] = None  # ai-tech, finance, psychology


class WorkflowRunOut(BaseModel):
    id: str
    workflow_id: str
    channel: Optional[str]
    status: str
    session_id: Optional[str]
    output: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
