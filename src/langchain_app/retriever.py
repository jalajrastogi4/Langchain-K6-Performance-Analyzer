from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import BSHTMLLoader, UnstructuredHTMLLoader
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from pathlib import Path
from typing import Optional, List

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()


class ReportRetriever:
    
    def __init__(self):
        self.vectorstore = None
        self._embeddings = None
        self._retriever_cache = {}
    
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

    def _load_and_split_docs(self, report_name: str) -> List[Document]:
        """
        Load and split the report into document chunks.
        """
        try:
            if not report_name.endswith(".html"):
                file_path = Path(settings.REPORTS_DIR) / f"{report_name}.html"
            else:
                file_path = Path(settings.REPORTS_DIR) / report_name

            if not file_path.exists():
                raise FileNotFoundError(f"Report not found: {file_path}")

            logger.info(f"Creating document loader for: {report_name}")
            source_id = str(file_path.resolve().as_posix())

            try:
                logger.info(f"Using UnstructuredHTMLLoader for: {report_name}")
                loader = UnstructuredHTMLLoader(str(file_path))
            except Exception:
                logger.info(f"Using BSHTMLLoader for: {report_name}")
                loader = BSHTMLLoader(str(file_path))
            
            documents = loader.load()
            for doc in documents:
                doc.metadata["source"] = source_id
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            chunks = splitter.split_documents(documents)

            logger.info(f"Loaded {len(chunks)} chunks from {report_name}")
            return chunks
        except Exception as e:
            logger.error(f"Failed to load and split docs: {e}")
            raise
    
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
                
            return report_files[0]
            
        except Exception as e:
            logger.error(f"Failed to load report: {e}")
            raise
    
    # def load_specific_report(self, report_name: str) -> str:
    #     """
    #     Load a specific report by filename.
    #     """
    #     try:
    #         if not report_name.endswith('.html'):
    #             report_path = Path(settings.REPORTS_DIR) / f"{report_name}.html"
    #         else:
    #             report_path = Path(settings.REPORTS_DIR) / report_name
    #         if not report_path.exists():
    #             raise FileNotFoundError(f"Report not found: {report_path}")
            
    #         logger.info(f"Loading specific report: {report_name}")
    #         return report_path.read_text(encoding="utf-8")
            
    #     except Exception as e:
    #         logger.error(f"Failed to load specific report {report_name}: {e}")
    #         raise
    
    def build_retriever(self, report_name: Optional[str] = None, collection_name: str = "performance_reports"):
        """
        Create a retriever for report content.
        """
        try:
            
            if report_name is None:
                report_name = self.load_latest_report()

            if report_name in self._retriever_cache:
                return self._retriever_cache[report_name]

            chunks = self._load_and_split_docs(report_name)
            chroma_dir = Path(settings.CHROMADB_DIR)

            if chroma_dir.exists():
                logger.info(f"Loading existing vectorstore from {chroma_dir}")
                self.vectorstore = Chroma(
                    persist_directory=str(chroma_dir),
                    embedding_function=self.embeddings,
                    collection_name=collection_name,
                )

                existing_sources = set()

                try:
                    all_docs = self.vectorstore.get(include=["metadatas"])
                    if "metadatas" in all_docs:
                        for meta in all_docs["metadatas"]:
                            if meta and "source" in meta:
                                existing_sources.add(meta["source"])
                except Exception as e:
                    logger.warning(f"Could not fetch existing sources cleanly: {e}")

                new_chunks = [doc for doc in chunks if doc.metadata.get("source") not in existing_sources]

                if new_chunks:
                    logger.info(f"Adding {len(new_chunks)} new chunks from {report_name}")
                    self.vectorstore.add_documents(new_chunks)
                    self.vectorstore.persist()
                else:
                    logger.info(f"No new documents to add from {report_name}")
            
            else:
                logger.info(f"Creating new vectorstore in {chroma_dir}")
                self.vectorstore = Chroma.from_documents(
                    chunks,
                    self.embeddings,
                    persist_directory=str(chroma_dir),
                    collection_name=collection_name,
                )
                self.vectorstore.persist()

            retriever = self.vectorstore.as_retriever(search_kwargs={"k": settings.MAX_RETRIEVAL_DOCS})

            self._retriever_cache[report_name] = retriever

            return retriever
            
        except Exception as e:
            logger.error(f"Failed to build retriever: {e}")
            raise RuntimeError(f"Retriever creation failed: {e}")
    
    def update_vectorstore(self, new_report_name: str) -> None:
        """
        Update vectorstore with a new report (defaults to latest).
        """
        try:
            self.build_retriever(new_report_name)
            logger.info(f"Vectorstore updated with report: {new_report_name or 'latest'}")
            
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
