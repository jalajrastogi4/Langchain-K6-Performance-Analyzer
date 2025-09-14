import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Depends, Form
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
from src.app.schemas.requests import FileUploadMetadata
from src.app.schemas.responses import UploadResponse
from src.app.services.ingestion_service import IngestionService
from src.app.services.job_service import JobService
from src.app.schemas.job_schema import JobResponse, InternalJobCreateRequest
from src.app.models.jobs import JobType
from src.app.core.db import get_session
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.workers.tasks.ingestion_tasks import process_file_ingestion

logger = get_logger()


router = APIRouter(prefix="/upload")

@router.post("/upload_file")
async def upload_file(
    file: UploadFile = File(...), 
    metadata: Optional[str] = Form(None), 
    session: AsyncSession = Depends(get_session),
    ) -> UploadResponse:
    """
    Upload a file to the server.
    """
    try:
        ingestion_service = IngestionService(session)
        job_service = JobService(session)

        parsed_metadata = None
        if metadata:
            parsed_metadata = FileUploadMetadata(**json.loads(metadata))
        
        response, ingestion_job_id = await ingestion_service.save_upload_file(file, parsed_metadata)
        
        internal_job = InternalJobCreateRequest(
            job_type=JobType.ingestion,
            file_id=response.file_id,
            ingestion_job_id=ingestion_job_id,
        )

        job = await job_service.create_job(internal_job)

        process_file_ingestion.delay(job.id, ingestion_job_id, response.file_id)

        logger.info(f"File {file.filename} upload completed. Job {job.id} queued for ingestion.")

        response.job_id = job.id
        return response
    except Exception as e:
        logger.error(f"Error uploading file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-redundant/{job_id}")
async def start_ingestion(
    job_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Start data ingestion into database for an uploaded file using the job id. (REDUNDANT - USE ASYNC VERSION INSTEAD)
    """
    try:
        ingestion_service = IngestionService(session)
        job = await ingestion_service.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "pending":
            raise HTTPException(status_code=400, detail=f"Job already {job.status}")
        
        await ingestion_service.ingest_file_to_db(job.id, job.file_id)

        updated_job = await ingestion_service.get_job_by_id(job.id)
        
        return {
            "message": "Ingestion completed", 
            "job_id": updated_job.id,
            "status": updated_job.status,
            "total_rows": updated_job.total_rows,
            "rows_ingested": updated_job.rows_ingested,
            "started_at": updated_job.started_at,
            "finished_at": updated_job.finished_at,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_upload_job_status(
    job_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get status of a ingestion job
    """
    try:
        job_service = JobService(session)
        job = await job_service.get_job_by_id(job_id)

        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.job_type != JobType.ingestion:
            logger.error(f"Job {job_id} is not an ingestion job")
            raise HTTPException(status_code=400, detail="Job is not an ingestion job")
        
        return job_service.job_to_response(job)
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_id}/jobs", response_model=List[JobResponse])
async def get_file_jobs(
    file_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get all jobs for a specific file.
    """
    try:
        job_service = JobService(session)
        jobs = await job_service.get_jobs_by_file_id(file_id)
        
        return [job_service.job_to_response(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error getting jobs for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
