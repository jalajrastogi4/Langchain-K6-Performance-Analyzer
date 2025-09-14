# src/app/models/job.py
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import func, Index
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum


class JobType(str, Enum):
    ingestion = "ingestion"
    analysis = "analysis"
    qa = "qa"


class JobStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    job_type: JobType = Field(index=True)
    status: JobStatus = Field(index=True, default=JobStatus.pending)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.current_timestamp()
        )
    )
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True)
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True)
    )
    
    # Reference IDs
    ingestion_job_id: Optional[int] = Field(default=None, foreign_key="ingestion_jobs.id", index=True)
    file_id: Optional[str] = Field(default=None, index=True)
    report_id: Optional[str] = Field(default=None, index=True)
    
    # Job data and results
    job_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(pg.JSONB))
    result_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(pg.JSONB))
    error_details: Optional[str] = Field(default=None)
    
    # Retry functionality
    retry_count: int = Field(default=0)
    can_retry: bool = Field(default=True)
    
    def __repr__(self):
        return f"<Job id={self.id} type={self.job_type} status={self.status}>"
    
    def is_completed(self) -> bool:
        return self.status in [JobStatus.completed, JobStatus.failed]
    
    def duration_seconds(self) -> Optional[float]:
        if self.started_at is None or self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()


Index("idx_jobs_type_status", Job.job_type, Job.status)
Index("idx_jobs_created_at", Job.created_at)
Index("idx_jobs_ingestion_job_id", Job.ingestion_job_id)
Index("idx_jobs_file_id", Job.file_id)
Index("idx_jobs_report_id", Job.report_id)
