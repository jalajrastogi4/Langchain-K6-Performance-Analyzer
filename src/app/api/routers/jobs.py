from fastapi import APIRouter, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from src.app.core.db import get_session
from src.app.services.job_service import JobService
from src.app.schemas.job_schema import JobResponse, JobRetryRequest
from src.app.core.logging import get_logger

logger = get_logger()

router = APIRouter(prefix="/jobs")

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get status and detail of a job
    """
    try:
        job_service = JobService(session)
        job = await job_service.get_job_by_id(job_id)

        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")

        return job_service.job_to_response(job)
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: int,
    request: JobRetryRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Retry failed job.
    """
    try:
        job_service = JobService(session)
        job = await job_service.retry_job(job_id)
        logger.info(f"Job {job_id} queued for retry")
        # TODO: trigger celery task
        return job_service.job_to_response(job)
    except Exception as e:
        logger.error(f"Error retrying job {job_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))