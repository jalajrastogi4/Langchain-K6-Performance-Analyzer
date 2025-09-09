from typing import Literal, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator, field_validator
import os

from src.app.core.logging import get_logger


logger = get_logger()


class Settings(BaseSettings):
    
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    PROJECT_NAME: str = ""
    PROJECT_DESCRIPTION: str = ""
    SITE_NAME: str = ""
    API_V1_STR: str = ""
    
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 0
    POSTGRES_DB: str = ""
    DATABASE_URL: str = ""
    DATABASE_URL_ASYNC: str = ""

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False
    DB_POOL_RECYCLE: int = 1800
    
    OPENAI_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    
    LLM_MODEL: str = "gpt-4-turbo"
    LLM_TEMPERATURE: float = 0.0
    EMBEDDINGS_MODEL: str = "text-embedding-3-small"
    
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100
    MAX_RETRIEVAL_DOCS: int = 4
    
    REPORTS_DIR: str = "data/reports"
    UPLOADS_DIR: str = "data/uploads"
    NORMALIZED_DATA_DIR: str = "data/normalized"
    RAW_DATA_DIR: str = "data/raw"
    CHROMADB_DIR: str = "data/chromadb"
    LOGS_DIR: str = "logs"
    
    RESERVOIR_SAMPLE_SIZE: int = 50000
    MAX_FILE_SIZE_MB: int = 2048
    CHUNK_PROCESSING_SIZE: int = 10000


    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    MAX_UPLOAD_SIZE_MB: int = 2048

    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672  
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    CELERY_BROKER_URL: str = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"
    CELERY_RESULT_BACKEND: str = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"
    
    model_config = SettingsConfigDict(
        env_file=".envs/.env.local",  
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True
    )


    @property
    def reports_path(self) -> Path:
        return Path(self.REPORTS_DIR)
    
    @property  
    def uploads_path(self) -> Path:
        return Path(self.UPLOADS_DIR)
    
    @property
    def chromadb_path(self) -> Path:
        return Path(self.CHROMADB_DIR)
    
    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property 
    def database_url_async_path(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL
    
    
    @field_validator('OPENAI_API_KEY')
    def validate_openai_key(cls, v):
        if not v:
            raise ValueError("OpenAI API key is required")
        if not v.startswith('sk-'):
            raise ValueError("OpenAI API key must start with 'sk-'")
        if len(v) < 20:
            raise ValueError("OpenAI API key must be at least 20 characters long")
        return v
    
    

settings = Settings()
