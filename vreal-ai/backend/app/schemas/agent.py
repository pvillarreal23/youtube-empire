from typing import Optional, List
from pydantic import BaseModel


class AgentOut(BaseModel):
    id: str
    name: str
    role: str
    tier: int = 5
    reports_to: Optional[str]
    direct_reports: List[str]
    collaborates_with: List[str]
    avatar_color: str
    department: str
    personality_trait: str = ""
    special_skill: str = ""
    weakness_to_watch: str = ""
    learning_focus: str = ""

    class Config:
        from_attributes = True


class AgentDetail(AgentOut):
    system_prompt: str
    file_path: str
