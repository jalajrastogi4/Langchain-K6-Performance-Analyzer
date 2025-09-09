import os
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException

from src.app.services.analysis_service import analysis_service

from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.schemas.responses import AnalysisResponse, QuestionAnswerResponse
from src.app.schemas.requests import AnalyzeRequest, QuestionRequest

logger = get_logger()

router = APIRouter(prefix="/analyze")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_report(
    request: AnalyzeRequest
    ):
    """
    Run LangChain analysis on an existing report.
    """
    try:

        results = await analysis_service.analyze_report(request)
        return results

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.post("/ask", response_model=QuestionAnswerResponse)
async def ask_question(
    request: QuestionRequest
):
    """
    Ask a custom question about the performance report.
    """
    try:
        
        answer = await analysis_service.ask_question(request)
        return answer

    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {e}")


