from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime


class ToolCallOut(BaseModel):
    id: str
    tool_name: str
    input_data: dict
    output_data: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MessageOut(BaseModel):
    id: str
    thread_id: str
    sender_type: str
    sender_agent_id: Optional[str]
    sender_name: Optional[str] = None
    content: str
    created_at: datetime
    status: str
    message_type: str = "text"
    tool_calls: Optional[List[ToolCallOut]] = None

    class Config:
        from_attributes = True


class ThreadOut(BaseModel):
    id: str
    subject: str
    created_at: datetime
    updated_at: datetime
    status: str
    participants: List[str]

    class Config:
        from_attributes = True


class ThreadWithMessages(ThreadOut):
    messages: List[MessageOut]


class CreateThread(BaseModel):
    subject: str
    recipient_agent_ids: List[str]
    content: str


class SendMessage(BaseModel):
    content: str
    recipient_agent_ids: Optional[List[str]] = None
