from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Index
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import func, text
from datetime import datetime, timezone
from typing import Optional, List


class IngestionJob(SQLModel, table=True):
    
    __tablename__ = "ingestion_jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    
    file_id: str = Field(index=True)
    file_type: str = Field(nullable=False)
    file_size_mb: Optional[float] = None
      
    status: str = Field(index=True)
    rows_ingested: Optional[int] = Field(nullable=True)
    total_rows: Optional[int] = Field(nullable=True)
    processing_errors_count: int = Field(default=0)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            onupdate=func.current_timestamp(),
            ),
        )
    started_at: Optional[datetime] = Field(
            sa_column=Column(pg.TIMESTAMP(timezone=False), nullable=True)  # ✅ Only specify in Column
        )
    finished_at: Optional[datetime] = Field(
            sa_column=Column(pg.TIMESTAMP(timezone=False), nullable=True)  # ✅ Only specify in Column
        )
    
    error_details: Optional[str] = Field(nullable=True)
    
    requests: List["RequestLog"] = Relationship(back_populates="job")

    def __repr__(self):
        return f"<IngestionJob id={self.id} file_id={self.file_id} status={self.status} rows={self.rows_ingested}>"
    
    def calculate_progress_percentage(self) -> Optional[float]:
        if self.total_rows is None or self.total_rows == 0:
            return None
        return 100.0 if self.rows_ingested >= self.total_rows else (self.rows_ingested / self.total_rows) * 100
    
    def is_completed(self) -> bool:  
        if self.status in ["completed", "failed"]:
            return True
        return False
    
    def duration_seconds(self) -> Optional[float]:
        if self.started_at is None or self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()



Index('ix_ingestion_jobs_status_created', IngestionJob.status, IngestionJob.created_at)
Index('ix_ingestion_jobs_file_type', IngestionJob.file_type)
Index('ix_ingestion_jobs_finished_at', IngestionJob.finished_at)