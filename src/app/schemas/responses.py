from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.app.schemas.common import BaseResponse, MetadataInfo, ValidationResult


class HealthResponse(BaseResponse):
    status: str = Field(description="The status of the API")
    version: Optional[str] = Field(default=None, description="The version of the API")


class UploadResponse(BaseResponse):
    file_id: str = Field(description="The unique identifier for the uploaded file")
    file_path: str = Field(description="The path where the file was stored")
    validation: ValidationResult = Field(description="The file validation status")
    file_size_mb: float = Field(description="The size of the file in megabytes")
    job_id: Optional[int] = Field(default=None, description="The unique identifier for the job")


class ReportResponse(BaseResponse):
    report_id: str = Field(description="The unique identifier for the generated report")
    report_path: str = Field(description="The path where the HTML report was saved")
    file_id: str = Field(description="The unique identifier for the uploaded file")
    processing_time_seconds: Optional[float] = Field(default=None, description="The time taken to generate the report in seconds")


class AnalysisResponse(BaseResponse):
    executive_summary: str = Field(description="The main analysis summary")
    anomaly_detection: str = Field(description="The detected anomalies in the performance report")
    optimization_recommendations: str = Field(description="The suggested improvements to the performance report")
    qa_insights: str = Field(description="The question and answer insights")
    metadata: MetadataInfo = Field(description="The analysis metadata")
    report_id: str = Field(description="The unique identifier for the generated report")


class QuestionAnswerResponse(BaseResponse):
    question: str = Field(description="The original question asked")
    answer: str = Field(description="The LangChain generated answer")
    report_id: str = Field(description="The unique identifier for the generated report")
    confidence_score: Optional[float] = Field(default=None, description="The confidence score of the answer")


class MetricsResponse(BaseResponse):
    global_metrics: Dict[str, Any] = Field(description="The overall performance stats")
    endpoint_metrics: List[Dict[str, Any]] = Field(description="The per-endpoint stats")
    summary_stats: Dict[str, Any] = Field(description="The key numbers for the dashboard")
    file_id: str = Field(description="The unique identifier for the uploaded file")

