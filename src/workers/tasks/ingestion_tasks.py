from celery import current_task
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker

from src.workers.celery_config import celery_app
from src.app.services.ingestion_service import IngestionService
from src.app.services.job_service import JobService
from src.app.models.jobs import JobStatus
from src.app.core.config import settings
from src.app.core.db import db_manager
from src.app.core.logging import get_logger

logger = get_logger()


@celery_app.task(bind=True, name="process_file_ingestion", queue="ingestion")
def process_file_ingestion(self, job_id: int, ingestion_job_id: int, file_id: str):
    """
    Celery task wrapper for file ingestion process.
    """
    try:
        import asyncio
        return asyncio.run(_process_file_ingestion_async(job_id, ingestion_job_id, file_id))
    except Exception as e:
        logger.error(f"Ingestion failed for job {job_id}: {str(e)}")
        raise


async def _process_file_ingestion_async(job_id: int, ingestion_job_id: int, file_id: str):
    """
    Celery based async implementation of file ingestion with job status updates.
    """
    async with db_manager.async_session_factory() as session:
        job_service = JobService(session)
        ingestion_service = IngestionService(session)
        try:
            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.in_progress,
                started_at=datetime.utcnow(),
            )

            logger.info(f"Starting ingestion for job {job_id}, file {file_id}")

            await ingestion_service.ingest_file_to_db_with_staging(ingestion_job_id, file_id)

            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.completed,
                finished_at=datetime.utcnow(),
                result_data={
                    "message": "Ingestion completed successfully",
                    "file_id": file_id,
                    "ingestion_job_id": ingestion_job_id
                }
            )

            logger.info(f"Ingestion completed for job {job_id}")
            return {"status": "completed", "job_id": job_id}

        except Exception as e:
            logger.error(f"Ingestion failed for job {job_id}: {str(e)}")

            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.failed,
                finished_at=datetime.utcnow(),
                error_details=str(e)
            )

            raise

