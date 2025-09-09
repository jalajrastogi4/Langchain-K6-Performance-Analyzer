from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Index
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import func, text
from datetime import datetime, timezone
from typing import Optional, List


class RequestLog(SQLModel, table=True):
    
    __tablename__ = "request_logs"
    
    
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    
    job_id: int = Field(foreign_key="ingestion_jobs.id", index=True)
    
    timestamp: datetime = Field(nullable=False)
    url: str = Field(index=True)
    method: str = Field(nullable=False)
    status_code: int = Field(index=True, nullable=False)
    success: bool = Field(nullable=False)
    
    response_time_ms: float = Field(index=True, nullable=False)
    
    blocked_ms: Optional[float] = Field(default=None)
    connecting_ms: Optional[float] = Field(default=None)
    receiving_ms: Optional[float] = Field(default=None)
    sending_ms: Optional[float] = Field(default=None)
    tls_handshake_ms: Optional[float] = Field(default=None)
    waiting_ms: Optional[float] = Field(default=None)
    
    job: Optional["IngestionJob"] = Relationship(back_populates="requests")

    def __repr__(self):
        return f"<RequestLog id={self.id} job={self.job_id} method={self.method} url={self.url} status_code={self.status_code} response_time_ms={self.response_time_ms}>"
    
    def is_error(self) -> bool:
        return self.status_code >= 400 if self.status_code is not None else False
    
    def is_slow(self, threshold_ms: float = 1000.0) -> bool:
        if self.response_time_ms is None:
            return False
        return self.response_time_ms > threshold_ms


Index('ix_request_logs_job_timestamp', RequestLog.job_id, RequestLog.timestamp)
Index('ix_request_logs_url_status', RequestLog.url, RequestLog.status_code)
Index('ix_request_logs_response_time', RequestLog.response_time_ms)
Index('ix_request_logs_timestamp', RequestLog.timestamp)



