import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class LangChainSettings:
    
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    
    
    embeddings_model: str = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
    
    reports_dir: str = os.getenv("REPORTS_DIR", "data/reports")
    chromadb_dir: str = os.getenv("CHROMADB_DIR", "data/chromadb")
    normalized_data_dir: str = os.getenv("NORMALIZED_DATA_DIR", "data/normalized")
    raw_data_dir: str = os.getenv("RAW_DATA_DIR", "data/raw")
    
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    max_retrieval_docs: int = int(os.getenv("MAX_RETRIEVAL_DOCS", "4"))
    
    langchain_tracing_v2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    
    def __post_init__(self):
        """
        Validate configuration after initialization.
        """
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Please set it in your .env file."
            )
        
        for dir_path in [self.reports_dir, self.chromadb_dir, self.normalized_data_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @property 
    def reports_path(self) -> Path:
        """
        Get reports directory as Path object.
        """
        return Path(self.reports_dir)
    
    @property
    def chromadb_path(self) -> Path:
        """
        Get ChromaDB directory as Path object.
        """
        return Path(self.chromadb_dir)



_settings: Optional[LangChainSettings] = None


def get_langchain_settings() -> LangChainSettings:
    """
    Get LangChain settings.
    """
    global _settings
    if _settings is None:
        _settings = LangChainSettings()
    return _settings

