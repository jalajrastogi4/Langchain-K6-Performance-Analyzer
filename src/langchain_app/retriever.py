from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
from typing import Optional, List

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()


class ReportRetriever:
    
    def __init__(self):
        self.vectorstore = None
        self._embeddings = None
    
    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """
        initialize embeddings model.
        """
        if self._embeddings is None:
            try:
                self._embeddings = OpenAIEmbeddings(
                    model=settings.EMBEDDINGS_MODEL,
                    openai_api_key=settings.OPENAI_API_KEY
                )
                logger.info(f"Initialized embeddings model: {settings.EMBEDDINGS_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
                raise RuntimeError(f"Embeddings initialization failed: {e}")
        return self._embeddings
    
    def load_latest_report(self) -> str:
        """
        Load the most recently generated report.
        """
        try:
            reports_path = Path(settings.REPORTS_DIR)
            if not reports_path.exists():
                raise FileNotFoundError(f"Reports directory does not exist: {reports_path}")
            
            
            report_files = sorted(
                reports_path.glob("*.html"), 
                key=lambda f: f.stat().st_mtime, 
                reverse=True
            )
            
            if not report_files:
                raise FileNotFoundError(f"No HTML reports found in {reports_path}")
            
            latest_report = report_files[0]
            logger.info(f"Loading report: {latest_report.name}")
            
            content = latest_report.read_text(encoding="utf-8")
            if not content.strip():
                raise IOError(f"Report file is empty: {latest_report}")
                
            return content
            
        except Exception as e:
            logger.error(f"Failed to load report: {e}")
            raise
    
    def load_specific_report(self, report_name: str) -> str:
        """
        Load a specific report by filename.
        """
        try:
            if not report_name.endswith('.html'):
                report_path = Path(settings.REPORTS_DIR) / f"{report_name}.html"
            else:
                report_path = Path(settings.REPORTS_DIR) / report_name
            if not report_path.exists():
                raise FileNotFoundError(f"Report not found: {report_path}")
            
            logger.info(f"Loading specific report: {report_name}")
            return report_path.read_text(encoding="utf-8")
            
        except Exception as e:
            logger.error(f"Failed to load specific report {report_name}: {e}")
            raise
    
    def build_retriever(self, report_content: Optional[str] = None, collection_name: str = "performance_reports"):
        """
        Create a retriever for report content.
        """
        try:
            
            if report_content is None:
                report_content = self.load_latest_report()
            
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            chunks = splitter.split_text(report_content)
            if not chunks:
                raise ValueError("No text chunks created from report content")
            
            logger.info(f"Created {len(chunks)} text chunks for embedding")
            
           
            self.vectorstore = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                persist_directory=str(Path(settings.CHROMADB_DIR)),
                collection_name=collection_name
            )
            
            
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": settings.MAX_RETRIEVAL_DOCS}
            )
            
            logger.info(f"Successfully created retriever with {len(chunks)} documents")
            return retriever
            
        except Exception as e:
            logger.error(f"Failed to build retriever: {e}")
            raise RuntimeError(f"Retriever creation failed: {e}")
    
    def update_vectorstore(self, new_report_content: str) -> None:
        """
        Update existing vector store with new report content.
        """
        try:
            if self.vectorstore is None:
                logger.warning("No existing vectorstore. Creating new one.")
                self.build_retriever(new_report_content)
                return
            
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            new_chunks = splitter.split_text(new_report_content)
            
            
            self.vectorstore.add_texts(new_chunks)
            logger.info(f"Added {len(new_chunks)} new chunks to vectorstore")
            
        except Exception as e:
            logger.error(f"Failed to update vectorstore: {e}")
            raise
    


def load_latest_report() -> str:
    """
    Load the latest report.
    """
    retriever = ReportRetriever()
    return retriever.load_latest_report()


def build_retriever(persist_dir: Optional[str] = None) -> object:
    """
    Build a retriever.
    """
    if persist_dir:
        settings.chromadb_dir = persist_dir
    
    retriever_manager = ReportRetriever()
    return retriever_manager.build_retriever()
