from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from typing import Dict, Any, List

from src.app.schemas.common import GlobalMetrics, EndpointMetrics
from src.app.schemas.responses import ReportResponse
from src.eda.report_generator import ReportGenerator
from src.eda.plots import generate_all_plots

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()

class ReportService:
    def __init__(self):
        self.report_generator = ReportGenerator()

    async def generate_report(
        self, file_id: str, global_metrics: GlobalMetrics, endpoint_metrics: List[EndpointMetrics], 
        output_dir: str = settings.REPORTS_DIR) -> ReportResponse:
        try:

            start = datetime.now()

            global_metrics_dict = global_metrics.model_dump()
            endpoint_metrics_dict = [endpoint_metrics.model_dump() for endpoint_metrics in endpoint_metrics]
            # Generate plots
            plots = generate_all_plots(global_metrics_dict, endpoint_metrics_dict)

            # Report path
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"report_{file_id}.html"

            # Generate final report
            self.report_generator.generate_report(global_metrics_dict, endpoint_metrics_dict, plots, str(output_file))

            return ReportResponse(
                report_id=f"report_{file_id}",
                report_path=str(output_file),
                file_id=file_id,
                processing_time = (datetime.now() - start).total_seconds(),
            )
        except Exception as e:
            logger.error(f"Error generating report for file_id {file_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

    async def get_report(self, file_id: str, output_dir: str = settings.REPORTS_DIR) -> str:
        path = Path(output_dir) / f"report_{file_id}.html"
        if not path.exists():
            logger.error(f"Report not found for file_id {file_id}")
            raise HTTPException(status_code=404, detail="Report not found")
        return str(path)
