from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class MessageOut(BaseModel):
    id: str
    thread_id: str
    sender_type: str
    sender_agent_id: Optional[str]
    content: str
    created_at: datetime
    status: str

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
