from pydantic import BaseModel, Field, computed_field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from src.app.models.jobs import JobType, JobStatus


class AnalysisType(str, Enum):
    executive_summary = "executive_summary"
    anomaly = "anomaly"
    optimization = "optimization"

class InternalJobCreateRequest(BaseModel):
    job_type: JobType
    file_id: Optional[str] = None
    report_id: Optional[str] = None
    ingestion_job_id: Optional[int] = None
    job_data: Optional[Dict[str, Any]] = None


class JobRetryRequest(BaseModel):
    force_retry: bool = Field(default=False, description="Force retry even if can_retry is False")


class JobResponse(BaseModel):
    id: int
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    file_id: Optional[str] = None
    report_id: Optional[str] = None
    ingestion_job_id: Optional[int] = None
    
    job_data: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    
    retry_count: int = 0
    can_retry: bool = True

    message: str = Field(default="",description="Response message")

    @computed_field
    def success(self) -> bool:
        return self.status == JobStatus.completed
    
    @computed_field
    def duration_seconds(self) -> Optional[float]:
        if not (self.started_at and self.finished_at):
            return None
        return (self.finished_at - self.started_at).total_seconds()
    
    
