from pydantic import BaseModel, field_validator
from typing import Optional


class ResearchRequest(BaseModel):
    topic: str
    model: Optional[str] = None

    @field_validator("topic")
    @classmethod
    def topic_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Topic cannot be empty")
        if len(v) < 5:
            raise ValueError("Topic must be at least 5 characters")
        if len(v) > 500:
            raise ValueError("Topic must be under 500 characters")
        return v


class ResearchStartResponse(BaseModel):
    report_id: str
    status: str
    message: str


class AgentProgressEvent(BaseModel):
    type: str          # "agent_start" | "agent_complete" | "agent_error" | "complete" | "error"
    agent: Optional[str] = None
    message: str
    report_id: str
    data: Optional[dict] = None
