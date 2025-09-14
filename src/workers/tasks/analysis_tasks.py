from celery import current_task
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker

from src.workers.celery_config import celery_app
from src.app.schemas.requests import AnalyzeRequest, QuestionRequest
from src.app.services.analysis_service import AnalysisService
from src.app.services.job_service import JobService
from src.app.models.jobs import JobStatus
from src.app.core.config import settings
from src.app.core.db import db_manager
from src.app.core.logging import get_logger

logger = get_logger()


@celery_app.task(bind=True, name="process_report_analysis")
def process_report_analysis(self, job_id: int, analysis_request: dict):
    """
    Celery task wrapper for report analysis.
    """
    try:
        import asyncio
        return asyncio.run(_process_report_analysis_async(job_id, analysis_request))
    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {str(e)}")
        raise


async def _process_report_analysis_async(job_id: int, analysis_request: dict):
    """
    Celery based async implementation of report analysis with job status updates.
    """
    async with db_manager.async_session_factory() as session:
        job_service = JobService(session)
        analysis_service = AnalysisService(session)
        analysis_request = AnalyzeRequest(**analysis_request)

        try:
            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.in_progress,
                started_at=datetime.now(timezone.utc)
            )

            logger.info(f"Starting analysis for job {job_id}, report {analysis_request.report_id}")

            results = await analysis_service.analyze_report(analysis_request)

            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.completed,
                finished_at=datetime.now(timezone.utc),
                result_data={
                    "executive_summary": results.executive_summary,
                    "anomaly_detection": results.anomaly_detection,
                    "optimization_recommendations": results.optimization_recommendations,
                    "qa_insights": results.qa_insights,
                    "metadata": results.metadata.model_dump() if results.metadata else None
                }
            )

            logger.info(f"Analysis completed for job {job_id}")
            return {"status": "completed", "job_id": job_id}

        except Exception as e:
            logger.error(f"Analysis failed for job {job_id}: {str(e)}")

            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.failed,
                finished_at=datetime.now(timezone.utc),
                error_details=str(e)
            )
            
            raise


@celery_app.task(bind=True, name="process_qa_question")
def process_qa_question(self, job_id: int, question_request: dict):
    """
    Celery task wrapper for Q&A processing.
    """
    try:
        import asyncio
        return asyncio.run(_process_qa_question_async(job_id, question_request))
    except Exception as e:
        logger.error(f"Q&A failed for job {job_id}: {str(e)}")
        raise


async def _process_qa_question_async(job_id: int, question_request: dict):
    """
    Celery based async implementation of Q&A processing with job status updates.
    """

    async with db_manager.async_session_factory() as session:
        job_service = JobService(session)
        analysis_service = AnalysisService(session)
        question_request = QuestionRequest(**question_request)
        try:
            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.in_progress,
                started_at=datetime.now(timezone.utc)
            )

            logger.info(f"Starting Q&A for job {job_id}, report {question_request.report_id}")

            results = await analysis_service.ask_question(question_request)

            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.completed,
                finished_at=datetime.now(timezone.utc),
                result_data={
                    "question": results.question,
                    "answer": results.answer,
                    "report_id": results.report_id,
                    "confidence_score": results.confidence_score if results.confidence_score else None
                }
            )

            logger.info(f"Q&A completed for job {job_id}")
            return {"status": "completed", "job_id": job_id}

        except Exception as e:
            logger.error(f"Q&A failed for job {job_id}: {str(e)}")

            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.failed,
                finished_at=datetime.now(timezone.utc),
                error_details=str(e)
            )

            raise