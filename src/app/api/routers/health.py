from fastapi import APIRouter
from src.workers.celery_config import celery_app
router = APIRouter(prefix="/health")

@router.get("/health_check")
async def health_check():
    return {"status": "ok", "message": "API is healthy"}

@router.get("/celery")
def celery_health():
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        return {"status": "healthy", "workers": len(stats or {})}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}