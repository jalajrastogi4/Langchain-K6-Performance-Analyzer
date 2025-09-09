from fastapi import HTTPException
from typing import Dict, Any, List
from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.schemas.common import GlobalMetrics, EndpointMetrics

from src.app.models.ingestion_job import IngestionJob
from src.app.models.request_logs import RequestLog

from src.eda.metrics_db import MetricsDB, MetricsDB_Formatter

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()

class MetricsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.metrics_db = MetricsDB(self.session)
        self.metrics_db_formatter = MetricsDB_Formatter()

    async def get_global_metrics(self, job_id: int) -> GlobalMetrics:
        """
        Get the global metrics for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.calculate_global_metrics(job_id)
            formatted_metrics = self.metrics_db_formatter.format_global_metrics(raw_metrics)
            return formatted_metrics
        except Exception as e:
            logger.error(f"Error getting global metrics for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_endpoint_metrics(self, job_id: int) -> List[EndpointMetrics]:
        """
        Get the endpoint metrics for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.calculate_endpoint_metrics(job_id)
            formatted_metrics = self.metrics_db_formatter.format_endpoint_metrics(raw_metrics)
            return formatted_metrics
        except Exception as e:
            logger.error(f"Error getting endpoint metrics for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_rps_over_time(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Get the rps over time for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.rps_over_time(job_id)
            return raw_metrics
        except Exception as e:
            logger.error(f"Error getting rps over time for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_response_time_percentiles(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Get the response time percentiles for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.response_time_percentiles(job_id)
            return raw_metrics
        except Exception as e:
            logger.error(f"Error getting response time percentiles for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_error_rate_over_time(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Get the error rate over time for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.error_rate_over_time(job_id)
            return raw_metrics
        except Exception as e:
            logger.error(f"Error getting error rate over time for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_slowest_endpoints(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Get the slowest endpoints for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.slowest_endpoints(job_id)
            return raw_metrics
        except Exception as e:
            logger.error(f"Error getting slowest endpoints for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_error_distribution_by_endpoint(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Get the error distribution by endpoint for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.error_distribution_by_endpoint(job_id)
            return raw_metrics
        except Exception as e:
            logger.error(f"Error getting error distribution by endpoint for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_status_code_distribution(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Get the status code distribution for the job id.
        """
        try:
            raw_metrics = await self.metrics_db.status_code_distribution(job_id)
            return raw_metrics
        except Exception as e:
            logger.error(f"Error getting status code distribution for job_id {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))