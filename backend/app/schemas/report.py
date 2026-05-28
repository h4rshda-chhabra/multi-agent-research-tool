from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SourceOut(BaseModel):
    id: str
    url: str
    title: str
    domain: str
    snippet: Optional[str]
    published_date: Optional[str]
    relevance_score: float
    credibility_score: float
    recency_score: float
    technical_depth_score: float
    total_score: float

    model_config = {"from_attributes": True}


class AgentRunOut(BaseModel):
    id: str
    agent_name: str
    status: str
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: str
    user_id: str
    topic: str
    status: str
    markdown_content: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    sources: list[SourceOut] = []
    agent_runs: list[AgentRunOut] = []
    is_saved: bool = False

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: str
    topic: str
    status: str
    created_at: datetime
    is_saved: bool = False

    model_config = {"from_attributes": True}


class ExportRequest(BaseModel):
    report_id: str
    format: str  # "pdf" | "markdown"


class SaveReportRequest(BaseModel):
    report_id: str
