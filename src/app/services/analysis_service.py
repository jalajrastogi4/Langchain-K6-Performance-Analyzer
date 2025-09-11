from pathlib import Path
from fastapi import HTTPException

from src.langchain_app.analyzer import PerformanceAnalyzer

from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.schemas.responses import AnalysisResponse, QuestionAnswerResponse, MetadataInfo
from src.app.schemas.requests import AnalyzeRequest, QuestionRequest

logger = get_logger()

class AnalysisService:

    def __init__(self):
        self.analyzer = PerformanceAnalyzer()

    async def analyze_report(
        self, request: AnalyzeRequest
        ) -> AnalysisResponse:
        """
        Analyze the report from the report id.
        """
        try:
            
            results = self.analyzer.analyze_report_from_name(request.report_id)

            return AnalysisResponse(
                executive_summary=results["executive_summary"],
                anomaly_detection=results["anomaly_detection"],
                optimization_recommendations=results["optimization_recommendations"],
                qa_insights=results["qa_insights"],
                metadata=MetadataInfo(**results["metadata"]),
                report_id=request.report_id,
                success=True,
                message="Analysis completed successfully",
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    async def ask_question(
        self, request: QuestionRequest
        ) -> QuestionAnswerResponse:
        """
        Ask a question about the report from the report id.
        """

        report_path = Path(settings.REPORTS_DIR) / f"{request.report_id}.html" if not request.report_id.endswith('.html') else Path(settings.REPORTS_DIR) / request.report_id

        if not report_path.exists():
            logger.error(f"Report not found: {request.report_id}")
            raise HTTPException(status_code=404, detail="Report not found")

        try:

            answer = self.analyzer.answer_question(request.question, request.report_id)

            return QuestionAnswerResponse(
                question=request.question,
                answer=answer,
                report_id=request.report_id,
                confidence_score=None,  
                success=True,
                message="Answer generated successfully",
            )
        
        except Exception as e:
            logger.error(f"Question answer failed: {e}")
            raise HTTPException(status_code=500, detail=f"Question answer failed: {e}")


analysis_service = AnalysisService()