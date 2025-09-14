from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Index
from sqlalchemy.dialects import postgresql as pg
from datetime import datetime
from typing import Optional

class RequestLogStaging(SQLModel, table=True):
    __tablename__ = "request_logs_staging"
    
    # No auto-increment primary key for staging
    id: Optional[int] = Field(default=None, primary_key=True)
    
    job_id: int = Field(nullable=False)  # No foreign key constraint
    
    timestamp: datetime = Field(nullable=False)
    url: str = Field(nullable=False)
    method: str = Field(nullable=False)
    status_code: int = Field(nullable=False)
    success: bool = Field(nullable=False)
    
    response_time_ms: float = Field(nullable=False)
    
    blocked_ms: Optional[float] = Field(default=None)
    connecting_ms: Optional[float] = Field(default=None)
    receiving_ms: Optional[float] = Field(default=None)
    sending_ms: Optional[float] = Field(default=None)
    tls_handshake_ms: Optional[float] = Field(default=None)
    waiting_ms: Optional[float] = Field(default=None)

# Minimal index for cleanup operations only
Index('ix_staging_job_id', RequestLogStaging.job_id)