from fastapi import APIRouter
from src.app.api.routers import upload, report, analyze, health

api_router = APIRouter()

api_router.include_router(upload.router)
api_router.include_router(report.router)
api_router.include_router(analyze.router)
api_router.include_router(health.router)