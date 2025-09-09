import os
import pandas as pd
import shutil
import uuid
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
from pathlib import Path
from typing import Tuple, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, update

from src.app.models.request_logs import RequestLog
from src.app.models.ingestion_job import IngestionJob
from src.app.schemas.requests import FileUploadMetadata
from src.app.schemas.responses import UploadResponse
from src.app.schemas.common import ValidationResult
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.ingestion.k6_json_ingestor import normalizer_k6_json
from src.ingestion.k6_csv_ingestor import normalizer_k6_csv


logger = get_logger()


class IngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # async def start_ingestion(self, job_config: JobConfigSchema) -> JobResponse:
    #     pass

    # async def get_ingestion_status(job_id: int) -> JobStatus:
    #     pass

    # async def list_ingestion_jobs() -> List[JobSummary]:
    #     pass

    async def save_upload_file(
        self, file: UploadFile, metadata: Optional[FileUploadMetadata] = None
        ) -> UploadResponse:
        """
        Save the uploaded file and create a ingestion job.
        """
        try:
        
            file_id = f"{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(settings.UPLOADS_DIR, file_id)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

            job = IngestionJob(
                file_id=file_id,
                file_type=file.content_type or Path(file.filename).suffix.replace(".", ""),
                file_size_mb=file_size_mb,
                status="pending",
                rows_ingested=0,
                total_rows=0,
                processing_errors_count=0,
                created_at=datetime.now(timezone.utc),
                started_at=None,
                finished_at=None,
                error_details=None,
            )

            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)

            if metadata:
                logger.info(
                    f"File {file.filename} uploaded successfully with job_id {job.id} "
                    f"(test_name={metadata.test_name}, env={metadata.environment})"
                )
            else:
                logger.info(f"File {file.filename} uploaded successfully with job_id {job.id}")
                

            return UploadResponse(
                file_id=file_id, 
                file_size_mb=file_size_mb,
                file_path=file_path,
                validation=ValidationResult(
                    is_valid=True,
                    file_format=file.content_type or Path(file.filename).suffix.replace(".", ""),
                    file_size_mb=file_size_mb
                )
            ), job.id

        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    async def get_job_by_file_id(self, file_id: str) -> IngestionJob | None:
        """
        Get the ingestion job by the file id.
        """
        try:
            statement = select(IngestionJob).where(IngestionJob.file_id == file_id)
            result = await self.session.exec(statement)
            job = result.scalar_one_or_none()
            return job
        except Exception as e:
            logger.error(f"Error getting job by file_id {file_id}: {e}")
            raise HTTPException(status_code=404, detail=str(e))


    async def get_job_by_id(self, job_id: int) -> IngestionJob | None:
        """
        Get the ingestion job by the job id.
        """
        try:
            statement = select(IngestionJob).where(IngestionJob.id == job_id)
            result = await self.session.exec(statement)
            job = result.scalar_one_or_none()
            return job
        except Exception as e:
            logger.error(f"Error getting job by id {job_id}: {e}")
            raise HTTPException(status_code=404, detail=str(e))


    
    async def ingest_file_to_db(
        self, job_id: int, file_id: str
        ) -> None:
        """
        Ingest the data from uploaded file to the database.
        """
        try:
            job = await self.get_job_by_id(job_id)

            if not job:
                logger.error(f"Job not found with id {job_id}")
                raise HTTPException(status_code=404, detail="Job not found")

            file_path = os.path.join(settings.UPLOADS_DIR, file_id)
            if not os.path.exists(file_path):
                logger.error(f"File not found with id {file_id}")
                raise HTTPException(status_code=404, detail="File not found")

            logger.info(f"Starting ingestion for job {job.id}, file={file_id}")
            total_rows = 0
            start_time = datetime.utcnow()
            
            print("Chunks generator....")
            ext = os.path.splitext(file_path)[-1].lower()
            if ext == ".json":
                chunk_generator = normalizer_k6_json(file_path, chunk_size=50000)
            elif ext == ".csv":
                reader = pd.read_csv(file_path, chunksize=50000)
                chunk_generator = (normalizer_k6_csv(chunk) for chunk in reader)
            else:
                logger.error(f"Unsupported file extension: {ext}")
                raise HTTPException(status_code=400, detail="Unsupported file extension")

            print("Chunks processor....")

            for df_chunk in chunk_generator:
                if df_chunk.empty:
                    continue
                rows = [
                    RequestLog(
                        job_id=job.id,
                        timestamp=row.get("timestamp"),
                        url=row.get("url"),
                        method=row.get("method"),
                        status_code=int(row.get("status") or 0),
                        success=row.get("success"),
                        response_time_ms=row.get("response_time_ms"),
                        blocked_ms=row.get("blocked_ms"),
                        connecting_ms=row.get("connecting_ms"),
                        receiving_ms=row.get("receiving_ms"),
                        sending_ms=row.get("sending_ms"),
                        tls_handshake_ms=row.get("tls_handshake_ms"),
                        waiting_ms=row.get("waiting_ms"),
                    )
                    for row in df_chunk.to_dict(orient="records")
                ]

                self.session.add_all(rows)
                # await self.session.commit()
                await self.session.flush()
                total_rows += len(rows)

            print("Chunks processed...")
            await self.session.exec(
                update(IngestionJob)
                .where(IngestionJob.id == job.id)
                .values(
                    status="completed",
                    total_rows=total_rows,
                    rows_ingested=total_rows,
                    started_at=start_time,
                    finished_at=datetime.utcnow(),
                )
            )


            await self.session.commit()

            logger.info(f"Ingestion completed for job {job.id}: {total_rows} rows")

        except Exception as e:
            logger.error(f"Error ingesting file to db: {e}")

            await self.session.rollback()

            await self.session.exec(
                update(IngestionJob)
                .where(IngestionJob.id == job.id)
                .values(status="failed", 
                        error_details=str(e), 
                        finished_at=datetime.now(timezone.utc)),
            )
            await self.session.commit()
            raise HTTPException(status_code=500, detail=str(e))