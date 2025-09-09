import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Depends, Form
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from src.app.schemas.requests import FileUploadMetadata
from src.app.schemas.responses import UploadResponse
from src.app.services.ingestion_service import IngestionService

from src.app.core.db import get_session
from src.app.core.config import settings
from src.app.core.logging import get_logger

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
        parsed_metadata = None
        if metadata:
            parsed_metadata = FileUploadMetadata(**json.loads(metadata))
        response, job_id = await ingestion_service.save_upload_file(file, parsed_metadata)
        logger.info(f"Request for File {file.filename} upload completed successfully with job_id {job_id}")
        return response
    except Exception as e:
        logger.error(f"Error uploading file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/{job_id}")
async def start_ingestion(
    job_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Start data ingestion into database for an uploaded file using the job id.
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

       