from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

BuildingType = Literal["residential", "commercial", "industrial", "mixed_use"]

class SiteInfo(BaseModel):
    width_m: float | None = Field(default=None, gt=0, le=10000)
    length_m: float | None = Field(default=None, gt=0, le=10000)
    clear_height_m: float | None = Field(default=None, gt=0, le=100)
    area_m2: float | None = Field(default=None, gt=0)

class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    building_type: BuildingType
    location: str = Field(min_length=2, max_length=160)
    brief: str = Field(min_length=5, max_length=6000)
    site: SiteInfo = Field(default_factory=SiteInfo)
    spaces: list[str] = Field(default_factory=list, max_length=100)
    constraints: list[str] = Field(default_factory=list, max_length=100)

class Project(ProjectCreate):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RunCreate(BaseModel):
    agents: list[str] | None = None

class AgentInfo(BaseModel):
    id: str
    name: str
    discipline: str
    description: str
    output_scope: str

class AgentResult(BaseModel):
    agent_id: str
    status: Literal["completed", "skipped", "error"]
    summary: str
    findings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    needs_professional_review: bool = True

class DesignRun(BaseModel):
    id: str
    project_id: str
    status: Literal["completed", "error"]
    created_at: datetime
    agents: list[AgentResult]
    coordination_notes: list[str]
    disclaimer: str

class ErrorResponse(BaseModel):
    detail: str
    extra: dict[str, Any] = Field(default_factory=dict)

class APISettingsUpdate(BaseModel):
    provider: Literal["demo", "openai_compatible"]
    base_url: str = Field(default="", max_length=500)
    model: str = Field(default="", max_length=200)
    api_key: str = Field(default="", max_length=1000)
    chat_history_enabled: bool = False
    chat_history_retention_days: int = Field(default=30, ge=1, le=365)

class ConceptDrawingRequest(BaseModel):
    name: str = Field(default="Concept", max_length=100)
    type: str = Field(default="commercial", max_length=50)
    width: float = Field(gt=0, le=200)
    length: float = Field(gt=0, le=500)
    height: float = Field(gt=0, le=20)
    brief: str = Field(default="", max_length=3000)
