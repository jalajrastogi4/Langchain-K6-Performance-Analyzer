import os
import pandas as pd

from pathlib import Path
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.core.db import get_session
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.schemas.responses import ReportResponse
from src.app.services.metrics_service import MetricsService
from src.app.services.report_service import ReportService
from src.app.services.ingestion_service import IngestionService

logger = get_logger()

router = APIRouter(prefix="/report")


@router.post("/generate-eda-report")
async def generate_eda_report(
    file_id: str = Query(..., description="Uploaded file ID"),
    session: AsyncSession = Depends(get_session),
    ) -> ReportResponse:
    """
    Generate a HTML report for the uploaded file.
    """
    try:
        report_service = ReportService()
        metrics_service = MetricsService(session)
        ingestion_service = IngestionService(session)

        job = await ingestion_service.get_job_by_file_id(file_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        global_metrics = await metrics_service.get_global_metrics(job.id)
        endpoint_metrics = await metrics_service.get_endpoint_metrics(job.id)

        response = await report_service.generate_report(file_id, global_metrics, endpoint_metrics)
        logger.info(f"Request for Report generation completed successfully with report_id {response.report_id}")
        return response
    except Exception as e:
        logger.error(f"Error generating report for file_id {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
