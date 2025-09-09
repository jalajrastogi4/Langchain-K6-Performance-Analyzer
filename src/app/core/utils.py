from src.app.core.config import settings, Settings
from src.app.core.logging import get_logger
from pathlib import Path

logger = get_logger()

def create_all_directories(settings: Settings) -> None:
    """
    Create all directories for the application.
    """
    try:
        for path in [
            settings.REPORTS_DIR, 
            settings.UPLOADS_DIR, 
            settings.CHROMADB_DIR, 
            settings.LOGS_DIR,
            settings.NORMALIZED_DATA_DIR,
            settings.RAW_DATA_DIR,
        ]:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        raise e