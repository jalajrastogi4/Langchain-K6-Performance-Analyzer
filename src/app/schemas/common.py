from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    success: bool = Field(default=True, description="whether the request was successful")
    timestamp: datetime = Field(default=datetime.now(), description="timestamp of the response")
    message: str = Field(default="Request Successful", description="message of the response")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        allow_population_by_field_name = True


class ErrorResponse(BaseResponse):
    success: bool = Field(default=False, description="whether the request was successful")
    error_code: str = Field(description="The HTTP status or custom error code")
    message: str = Field(default="Request Failed", description="message of the response")
    details: Optional[Dict[str, Any]] = Field(default=None, description="additional details about the error")
    timestamp: datetime = Field(default=datetime.now(), description="timestamp of the response")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetadataInfo(BaseModel):
    analysis_timestamp: str = Field(description="timestamp of the analysis")
    report_length_chars: int = Field(description="length of the analyzed content")
    llm_model: str = Field(description="model used for the analysis")
    embeddings_model: str = Field(description="model used for the embeddings")


class ValidationResult(BaseModel):
    is_valid: bool = Field(description="whether the file passed is valid")
    file_format: str = Field(description="format of the file should be csv or json")
    file_size_mb: float = Field(description="size of the file in MB. It should be less than 10000 MB")
    row_count: Optional[int] = Field(default=None, description="number of rows in the file")
    error_message: Optional[str] = Field(default=None, description="error message if the file is not valid")

class GlobalMetrics(BaseModel):
    total_requests: int = Field(description="total number of requests")
    success_rate: float = Field(description="success rate of the requests")
    failure_rate: float = Field(description="failure rate of the requests")
    median_response_time: float = Field(description="median response time of the requests")
    avg_response_time: float = Field(description="average response time of the requests")
    p90_response_time: float = Field(description="90th percentile response time of the requests")
    p95_response_time: float = Field(description="95th percentile response time of the requests")
    p99_response_time: float = Field(description="99th percentile response time of the requests")
    max_response_time: float = Field(description="maximum response time of the requests")
    min_response_time: float = Field(description="minimum response time of the requests")
    request_status_error: float = Field(description="error rate of the requests")
    rps: float = Field(description="requests per second")
    status_2xx: float = Field(description="2xx status code rate of the requests")
    status_3xx: float = Field(description="3xx status code rate of the requests")
    status_4xx: float = Field(description="4xx status code rate of the requests")
    status_5xx: float = Field(description="5xx status code rate of the requests")

class EndpointMetrics(BaseModel):
    url: str = Field(description="url of the endpoint")
    total_requests: int = Field(description="total number of requests")
    success_rate: float = Field(description="success rate of the requests")
    failure_rate: float = Field(description="failure rate of the requests")
    median_response_time: float = Field(description="median response time of the requests")
    avg_response_time: float = Field(description="average response time of the requests")
    p90_response_time: float = Field(description="90th percentile response time of the requests")
    p95_response_time: float = Field(description="95th percentile response time of the requests")
    p99_response_time: float = Field(description="99th percentile response time of the requests")
    max_response_time: float = Field(description="maximum response time of the requests")
    min_response_time: float = Field(description="minimum response time of the requests")
    tail_latency_gap: float = Field(description="tail latency gap of the requests")
    blocked_ms: float = Field(description="blocked time of the requests")
    connecting_ms: float = Field(description="connecting time of the requests")
    receiving_ms: float = Field(description="receiving time of the requests")
    sending_ms: float = Field(description="sending time of the requests")
    tls_handshake_ms: float = Field(description="tls handshake time of the requests")
    waiting_ms: float = Field(description="waiting time of the requests")
    request_status_error: float = Field(description="error rate of the requests")
    rps: float = Field(description="requests per second")
    status_2xx: float = Field(description="2xx status code rate of the requests")
    status_3xx: float = Field(description="3xx status code rate of the requests")
    status_4xx: float = Field(description="4xx status code rate of the requests")
    status_5xx: float = Field(description="5xx status code rate of the requests")