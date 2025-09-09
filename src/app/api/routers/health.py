from fastapi import APIRouter

router = APIRouter(prefix="/health")

@router.get("/health_check")
async def health_check():
    return {"status": "ok", "message": "API is healthy"}