from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.app.api.main import api_router
from src.app.core.db import db_manager, init_db
from src.app.core.utils import create_all_directories
from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Initializing database and directories...")
        create_all_directories(settings)
        await init_db()
        logger.info("Database and directories initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        await db_manager.async_engine.dispose()
        raise
    finally:
        logger.info("Shutting down database...")
        await db_manager.async_engine.dispose()
        
    

app = FastAPI(
    title=settings.PROJECT_NAME, 
    description=settings.PROJECT_DESCRIPTION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)