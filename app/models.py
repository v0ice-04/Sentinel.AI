from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, Field

class DeployEvent(BaseModel):
    service: str
    environment: Literal["production", "staging", "development"]
    change_type: Literal["db-migration", "code-deploy", "config-change", "rollback"]
    timestamp: datetime
    deployed_by: str | None = None
    pr_url: str | None = None

class IncidentReport(BaseModel):
    service: str
    severity: Literal["low", "medium", "high", "critical"]
    date: date
    root_cause: str
    resolution: str
    trigger: str
    downtime_minutes: int | None = None

class RiskAnalysis(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high"]
    reasoning: str
    recommendation: str
    memories_used: int
    analyzed_at: datetime

class MemoryItem(BaseModel):
    text: str
    fact_type: str
    context: str | None
    occurred_start: str | None
    retrieved_at: datetime

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    memory_bank: str
    timestamp: datetime
