from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from src.app.models.jobs import Job, JobType, JobStatus
from src.app.schemas.job_schema import InternalJobCreateRequest, JobResponse
from src.app.core.logging import get_logger

logger = get_logger()


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(self, request: InternalJobCreateRequest) -> Job:
        """
        Create a new job.
        """
        try:
            job = Job(
                job_type=request.job_type,
                file_id=request.file_id,
                report_id=request.report_id,
                ingestion_job_id=request.ingestion_job_id,
                job_data=request.job_data,
                status=JobStatus.pending
            )
            
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            
            logger.info(f"Created job {job.id} of type {job.job_type}")
            return job
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create job: {e}")
            raise

    
    async def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """
        Get job by ID.
        """
        try:
            statement = select(Job).where(Job.id == job_id)
            result = await self.session.exec(statement)

            logger.info(f"Got job {job_id}")
            job = result.scalar_one_or_none()
            return job
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise
        
    async def get_jobs_by_file_id(self, file_id: str, status: Optional[JobStatus] = None) -> List[Job]:
        """
        Get all jobs for a specific file.
        """
        try:
            statement = select(Job).where(Job.file_id == file_id).order_by(Job.created_at.desc())
            if status:
                statement = statement.where(Job.status == status)
            result = await self.session.exec(statement)

            logger.info(f"Got jobs for file {file_id}")
            jobs = result.all()
            return jobs
        except Exception as e:
            logger.error(f"Failed to get jobs for file {file_id}: {e}")
            raise
        
    async def get_jobs_by_report_id(self, report_id: str, status: Optional[JobStatus] = None) -> List[Job]:
        """
        Get all jobs for a specific report.
        """
        try:
            statement = select(Job).where(Job.report_id == report_id).order_by(Job.created_at.desc())
            if status:
                statement = statement.where(Job.status == status)
            result = await self.session.exec(statement)

            logger.info(f"Got jobs for report {report_id}")
            jobs = result.all()
            return jobs
        except Exception as e:
            logger.error(f"Failed to get jobs for report {report_id}: {e}")
            raise
        
    async def update_job_status(self, job_id: int, status: JobStatus, 
                               started_at: Optional[datetime] = None,
                               finished_at: Optional[datetime] = None,
                               error_details: Optional[str] = None,
                               result_data: Optional[Dict[str, Any]] = None) -> Job:
        """
        Update job status and related fields.
        """
        try:
            job = await self.get_job_by_id(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            job.status = status
            
            if started_at:
                job.started_at = started_at
            if finished_at:
                job.finished_at = finished_at
            if error_details:
                job.error_details = error_details
                job.can_retry = True
            if result_data:
                job.result_data = result_data
            
            await self.session.commit()
            await self.session.refresh(job)

            logger.info(f"Updated job {job_id} status to {status}")
            return job
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update job {job_id} status to {status}: {e}")
            raise

    
    async def retry_job(self, job_id: int, force_retry: bool = False) -> Job:
        """
        Retry a failed job.
        """
        try:
            job = await self.get_job_by_id(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                raise ValueError("Job not found")

            # Check for foreced retry
            if not force_retry and not job.can_retry:
                raise ValueError("Job cannot be retried")

            # Check if job is failed
            if not force_retry and job.status != JobStatus.failed:
                raise ValueError("Only failed jobs can be retried")

            job.status = JobStatus.pending
            job.retry_count += 1
            job.error_details = None
            job.started_at = None
            job.finished_at = None
            
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)

            logger.info(f"Job {job_id} retried (force={force_retry}, retry_count={job.retry_count})")
            return job
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to retry job {job_id}: {e}")
            raise

        
    def job_to_response(self, job: Job) -> JobResponse:
        """Convert Job model to JobResponse."""
        return JobResponse(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            file_id=job.file_id,
            report_id=job.report_id,
            ingestion_job_id=job.ingestion_job_id,
            job_data=job.job_data,
            result_data=job.result_data,
            error_details=job.error_details,
            retry_count=job.retry_count,
            can_retry=job.can_retry,
            message=f"Job {job.status}"
        )