from typing import Optional, List
from pydantic import BaseModel


class AgentOut(BaseModel):
    id: str
    name: str
    role: str
    reports_to: Optional[str]
    direct_reports: List[str]
    collaborates_with: List[str]
    avatar_color: str
    department: str
    tools: List[str] = []

    class Config:
        from_attributes = True


class AgentDetail(AgentOut):
    system_prompt: str
    file_path: str
