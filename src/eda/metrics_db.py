from typing import Dict, List, Any
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession
from src.app.core.logging import get_logger
from datetime import datetime

from src.app.schemas.common import GlobalMetrics, EndpointMetrics
from src.app.models.ingestion_job import IngestionJob
from src.app.models.request_logs import RequestLog

logger = get_logger()

class MetricsDB:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_global_metrics(self, job_id: int) -> Dict[str, Any]:
        """
        Calculate global metrics for a given job_id.
        """
        query = text("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as success_count,
                AVG(response_time_ms) as avg_response_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as median_response_time,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY response_time_ms) as p90_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time,
                MAX(response_time_ms) as max_response_time,
                MIN(response_time_ms) as min_response_time,
                MIN(timestamp) as min_timestamp,
                MAX(timestamp) as max_timestamp,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as status_2xx,
                SUM(CASE WHEN status_code >= 300 AND status_code < 400 THEN 1 ELSE 0 END) as status_3xx,
                SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as status_4xx,
                SUM(CASE WHEN status_code >= 500 AND status_code < 600 THEN 1 ELSE 0 END) as status_5xx
            FROM request_logs 
            WHERE job_id = :job_id
        """)
        result = await self.session.execute(query, {"job_id": job_id})
        row = result.mappings().first()
        return dict(row) if row else {}

    async def calculate_endpoint_metrics(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Calculate url wise metrics for a given job_id.
        """
        query = text("""
            SELECT 
                url,
                COUNT(*) as total_requests,
                SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as success_count,
                AVG(response_time_ms) as avg_response_time,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY response_time_ms) as median_response_time,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY response_time_ms) as p90_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time,
                MAX(response_time_ms) as max_response_time,
                MIN(response_time_ms) as min_response_time,
                AVG(COALESCE(blocked_ms, 0)) as avg_blocked_ms,
                AVG(connecting_ms) as avg_connecting_ms,
                AVG(receiving_ms) as avg_receiving_ms,
                AVG(sending_ms) as avg_sending_ms,
                AVG(tls_handshake_ms) as avg_tls_handshake_ms,
                AVG(waiting_ms) as avg_waiting_ms,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as status_2xx,
                SUM(CASE WHEN status_code >= 300 AND status_code < 400 THEN 1 ELSE 0 END) as status_3xx,
                SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as status_4xx,
                SUM(CASE WHEN status_code >= 500 AND status_code < 600 THEN 1 ELSE 0 END) as status_5xx,
                MIN(timestamp) as first_request,
                MAX(timestamp) as last_request
            FROM request_logs 
            WHERE job_id = :job_id 
            GROUP BY url
            ORDER BY total_requests DESC
        """)
        result = await self.session.execute(query, {"job_id": job_id})
        return list(result.mappings().all())

    async def rps_over_time(self, job_id: int) -> List[Dict[str, Any]]:
        """
        RPS over time — aggregates per second request count for trend plots
        """
        query = text("""
            SELECT 
                DATE_TRUNC('second', timestamp) as ts,
                COUNT(*) as requests
            FROM request_logs
            WHERE job_id = :job_id
            GROUP BY ts
            ORDER BY ts;
        """)
        result = await self.session.execute(query, {"job_id": job_id})
        return list(result.mappings().all())

    async def response_time_percentiles(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Response time percentiles — shows the 50th, 95th, and 99th percentiles per minute for response time
        """
        query = text("""
            SELECT 
                DATE_TRUNC('minute', timestamp) as ts,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as median,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95
            FROM request_logs
            WHERE job_id = :job_id
            GROUP BY ts
            ORDER BY ts;
        """)
        result = await self.session.execute(query, {"job_id": job_id})
        return list(result.mappings().all())

    async def error_rate_over_time(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Error rate over time — shows the error rate per minute
        """
        query = text("""
            SELECT 
                DATE_TRUNC('minute', timestamp) as ts,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)::float / COUNT(*) as error_rate
            FROM request_logs
            WHERE job_id = :job_id
            GROUP BY ts
            ORDER BY ts;
        """)
        result = await self.session.execute(query, {"job_id": job_id})
        return list(result.mappings().all())

    async def slowest_endpoints(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Slowest endpoints — shows the top 10 slowest endpoints by average latency
        """
        query = text("""
            SELECT 
                url,
                AVG(response_time_ms) as avg_latency
            FROM request_logs
            WHERE job_id = :job_id
            GROUP BY url
            ORDER BY avg_latency DESC
            LIMIT 10;
        """)
        result = await self.session.execute(query, {"job_id": job_id})
        return list(result.mappings().all())

    async def error_distribution_by_endpoint(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Error distribution by endpoint — shows the error rate per endpoint
        """
        query = text("""
            SELECT 
                url,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
                COUNT(*) as total_requests,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)::float / COUNT(*) as error_rate
            FROM request_logs
            WHERE job_id = :job_id
            GROUP BY url
            ORDER BY error_rate DESC;
            """)
        result = await self.session.execute(query, {"job_id": job_id})
        return list(result.mappings().all())

    async def status_code_distribution(self, job_id: int) -> List[Dict[str, Any]]:
        """
        Status code distribution — shows the distribution of status codes
        """
        query = text("""
            SELECT 
                status_code,
                COUNT(*) as count
            FROM request_logs
            WHERE job_id = :job_id
            GROUP BY status_code;
        """)
        result = await self.session.execute(query, {"job_id": job_id})
        return list(result.mappings().all())



class MetricsDB_Formatter:
    def format_global_metrics(self, raw: Dict[str, Any]) -> GlobalMetrics:
        """
        Format the global metrics.
        """
        total_requests = raw["total_requests"]
        if not total_requests:
            return {}
        duration_sec = (
            (raw["max_timestamp"] - raw["min_timestamp"]).total_seconds()
            if raw["min_timestamp"] and raw["max_timestamp"]
            else 0
        )
        return GlobalMetrics(
            total_requests=total_requests,
            success_rate=raw["success_count"] / total_requests,
            failure_rate=1 - (raw["success_count"] / total_requests),
            median_response_time=raw["median_response_time"],
            avg_response_time=raw["avg_response_time"],
            p90_response_time=raw["p90_response_time"],
            p95_response_time=raw["p95_response_time"],
            p99_response_time=raw["p99_response_time"],
            max_response_time=raw["max_response_time"],
            min_response_time=raw["min_response_time"],
            request_status_error=raw["error_count"] / total_requests,
            rps=total_requests / duration_sec if duration_sec > 0 else None,
            status_2xx=raw["status_2xx"] / total_requests,
            status_3xx=raw["status_3xx"] / total_requests,
            status_4xx=raw["status_4xx"] / total_requests,
            status_5xx=raw["status_5xx"] / total_requests,
        )

    def format_endpoint_metrics(self, raw_results: List[Dict[str, Any]]) -> List[EndpointMetrics]:
        """
        Format the endpoint metrics.
        """
        formatted = []
        for row in raw_results:
            total_requests = row["total_requests"] or 0
            success_count = row["success_count"] or 0
            first_request = row["first_request"]
            last_request = row["last_request"]

            duration_sec = 0
            if first_request and last_request and isinstance(first_request, datetime) and isinstance(last_request, datetime):
                duration_sec = (last_request - first_request).total_seconds()

            metrics = EndpointMetrics(
                url=row["url"],
                total_requests=total_requests,
                success_rate=success_count / total_requests if total_requests > 0 else None,
                failure_rate=1 - (success_count / total_requests) if total_requests > 0 else None,
                median_response_time=row["median_response_time"],
                avg_response_time=row["avg_response_time"],
                p90_response_time=row["p90_response_time"],
                p95_response_time=row["p95_response_time"],
                p99_response_time=row["p99_response_time"],
                max_response_time=row["max_response_time"],
                min_response_time=row["min_response_time"],
                tail_latency_gap=(row["p90_response_time"] - row["median_response_time"]) if row["p90_response_time"] and row["median_response_time"] else None,
                blocked_ms=row["avg_blocked_ms"],
                connecting_ms=row["avg_connecting_ms"],
                receiving_ms=row["avg_receiving_ms"],
                sending_ms=row["avg_sending_ms"],
                tls_handshake_ms=row["avg_tls_handshake_ms"],
                waiting_ms=row["avg_waiting_ms"],
                request_status_error=row["error_count"] / total_requests if total_requests > 0 else None,
                rps=total_requests / duration_sec if duration_sec > 0 else None,
                status_2xx=(row["status_2xx"] or 0) / total_requests if total_requests > 0 else None,
                status_3xx=(row["status_3xx"] or 0) / total_requests if total_requests > 0 else None,
                status_4xx=(row["status_4xx"] or 0) / total_requests if total_requests > 0 else None,
                status_5xx=(row["status_5xx"] or 0) / total_requests if total_requests > 0 else None,
            )
            formatted.append(metrics)
        return formatted
