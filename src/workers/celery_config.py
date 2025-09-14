from celery import Celery
from src.app.core.config import settings

celery_app = Celery(
    "langchain_performance_analyzer",
    broker=settings.CELERY_BROKER_URL,  # "pyamqp://guest@localhost//"
    backend=settings.CELERY_RESULT_BACKEND,  # "redis://localhost:6379/0"
    include=[
        "src.workers.tasks.ingestion_tasks",
        "src.workers.tasks.analysis_tasks"
    ]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_time_limit=2100,
    task_soft_time_limit=1800,
    task_max_retries=3,
    task_default_retry_delay=300,
    task_routes={
        'src.workers.tasks.ingestion_tasks.*': {'queue': 'ingestion'},
        'src.workers.tasks.analysis_tasks.*': {'queue': 'analysis'},
    }
)