from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    report_id: str = Field(description="The unique identifier for the generated report")
    analysis_type: Optional[str] = Field(default=None, description="The type of analysis to perform")
    include_recommendations: Optional[bool] = Field(default=True, description="Whether to include recommendations")


class QuestionRequest(BaseModel):
    question: str = Field(description="The question to ask")
    report_id: str = Field(description="The unique identifier for the generated report")
    context_type: Optional[str] = Field(default=None, description="The type of context to use")
    
    @field_validator('question')
    def validate_question_length(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Question must be at least 5 characters')
        return v.strip()



class ReportGenerationRequest(BaseModel):
    file_id: str = Field(description="The unique identifier for the uploaded file")
    report_format: Optional[str] = Field(default=None, description="The format of the report")
    include_charts: Optional[bool] = Field(default=True, description="Whether to include charts")
    chart_style: Optional[str] = Field(default=None, description="The style of the charts")


class FileUploadMetadata(BaseModel):
    test_name: Optional[str] = Field(default=None, description="The name of the performance test")
    environment: Optional[str] = Field(default=None, description="The test environment")
    test_duration_minutes: Optional[int] = Field(default=None, description="The duration of the test in minutes")
    expected_load: Optional[str] = Field(default=None, description="The expected load of the test")

