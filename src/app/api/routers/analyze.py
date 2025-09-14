import os
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from src.app.services.analysis_service import analysis_service

from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.schemas.responses import AnalysisResponse, QuestionAnswerResponse
from src.app.schemas.requests import AnalyzeRequest, QuestionRequest
from src.app.schemas.job_schema import JobResponse, InternalJobCreateRequest
from src.app.models.jobs import JobType
from src.app.core.db import get_session
from src.app.services.job_service import JobService
from src.workers.tasks.analysis_tasks import process_report_analysis, process_qa_question

logger = get_logger()

router = APIRouter(prefix="/analyze")


@router.post("/analyze-redundant", response_model=AnalysisResponse)
async def analyze_report(
    request: AnalyzeRequest
    ):
    """
    Run LangChain analysis on an existing report. (REDUNDANT - USE ASYNC VERSION INSTEAD)
    """
    try:

        results = await analysis_service.analyze_report(request)
        return results

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.post("/ask-redundant", response_model=QuestionAnswerResponse)
async def ask_question(
    request: QuestionRequest
):
    """
    Ask a custom question about the performance report. (REDUNDANT - USE ASYNC VERSION INSTEAD)
    """
    try:
        
        answer = await analysis_service.ask_question(request)
        return answer

    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {e}")


@router.post("/analyze-async", response_model=JobResponse)
async def analyze_report_async(
    request: AnalyzeRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Start asynchronous analysis of a report.
    """
    try:
        job_service = JobService(session)
        
        job_create_request = InternalJobCreateRequest(
            job_type=JobType.analysis,
            report_id=request.report_id,
            job_data={
                "analysis_type": request.analysis_type,
                "include_recommendations": request.include_recommendations
            }
        )
        
        job = await job_service.create_job(job_create_request)
        
        process_report_analysis.delay(job.id, request.model_dump())
        
        logger.info(f"Analysis job {job.id} created for report {request.report_id}")
        
        return job_service.job_to_response(job)
    except Exception as e:
        logger.error(f"Error creating analysis job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask-async", response_model=JobResponse)  
async def ask_question_async(
    request: QuestionRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Start asynchronous Q&A for a report.
    """
    try:
        job_service = JobService(session)
        
        job_create_request = InternalJobCreateRequest(
            job_type=JobType.qa,
            report_id=request.report_id,
            job_data={"question": request.question}
        )
        
        job = await job_service.create_job(job_create_request)
        
        process_qa_question.delay(job.id, request.model_dump())
        
        logger.info(f"Q&A job {job.id} created for report {request.report_id}")
        
        return job_service.job_to_response(job)
    except Exception as e:
        logger.error(f"Error creating Q&A job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_analysis_job_status(
    job_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get the status of an analysis or Q&A job.
    """
    try:
        job_service = JobService(session)
        job = await job_service.get_job_by_id(job_id)
        
        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.job_type not in [JobType.analysis, JobType.qa]:
            logger.error(f"Job {job_id} is not an analysis or Q&A job")
            raise HTTPException(status_code=400, detail="Job is not an analysis or Q&A job")
        
        return job_service.job_to_response(job)
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{report_id}/jobs", response_model=List[JobResponse])
async def get_report_jobs(
    report_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get all jobs for a specific report.
    """
    try:
        job_service = JobService(session)
        jobs = await job_service.get_jobs_by_report_id(report_id)
        
        return [job_service.job_to_response(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error getting jobs for report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
        