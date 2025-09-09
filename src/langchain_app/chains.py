from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain.schema import Document

import pandas as pd
from typing import Dict, Any, List
from .retriever import ReportRetriever
from .prompts import get_qa_prompt, get_summary_prompt

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()


class PerformanceChainManager:
    
    def __init__(self):
        """
        Initialize with configuration settings.
        """
        self.retriever_manager = ReportRetriever()
        self._llm = None
        self._retriever = None
    
    @property
    def llm(self) -> ChatOpenAI:
        """
        initialize LLM.
        """
        if self._llm is None:
            try:
                self._llm = ChatOpenAI(
                    model=settings.LLM_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    openai_api_key=settings.OPENAI_API_KEY
                )
                logger.info(f"Initialized LLM: {settings.LLM_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise RuntimeError(f"LLM initialization failed: {e}")
        return self._llm
    
    @property
    def retriever(self):
        """
        initialize retriever.
        """
        if self._retriever is None:
            try:
                self._retriever = self.retriever_manager.build_retriever()
                logger.info("Retriever initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize retriever: {e}")
                raise RuntimeError(f"Retriever initialization failed: {e}")
        return self._retriever
    
    def get_qa_chain(self):
        """
        Create Q&A chain.
        """
        try:
            
            qa_chain = (
                RunnableParallel({
                    "context": self.retriever | self._format_docs,
                    "question": RunnablePassthrough()
                })
                | get_qa_prompt()
                | self.llm
                | StrOutputParser()
            )
            
            logger.info("Q&A chain created successfully")
            return qa_chain
            
        except Exception as e:
            logger.error(f"Failed to create Q&A chain: {e}")
            raise RuntimeError(f"Q&A chain creation failed: {e}")
    
    def get_summary_chain(self):
        """
        Create summary chain.
        """
        try:
            
            summary_chain = (
                get_summary_prompt()
                | self.llm  
                | StrOutputParser()
            )
            
            logger.info("Summary chain created successfully")
            return summary_chain
            
        except Exception as e:
            logger.error(f"Failed to create summary chain: {e}")
            raise RuntimeError(f"Summary chain creation failed: {e}")
    
    def analyze_performance_report(self, report_content: str = None) -> Dict[str, Any]:
        """
        Comprehensive analysis of performance report.
        """
        try:
            
            if report_content:
                self.retriever_manager.update_vectorstore(report_content)
            
            
            summary_chain = self.get_summary_chain()
            latest_content = report_content or self.retriever_manager.load_latest_report()
            
            summary = summary_chain.invoke({"context": latest_content})
            
            # Generate specific insights using Q&A
            qa_chain = self.get_qa_chain()
            
            key_questions = [
                "What are the main performance bottlenecks identified?",
                "Which endpoints have the highest error rates?", 
                "What is the overall system performance assessment?",
                "What are the recommended optimizations?"
            ]
            
            insights = {}
            for question in key_questions:
                try:
                    answer = qa_chain.invoke(question)
                    insights[question] = answer
                except Exception as e:
                    logger.warning(f"Failed to answer question '{question}': {e}")
                    insights[question] = f"Analysis unavailable: {str(e)}"
            
            result = {
                "executive_summary": summary,
                "key_insights": insights,
                "report_analyzed": latest_content[:200] + "..." if latest_content else "No report content",
                "analysis_timestamp": pd.Timestamp.now().isoformat()
            }
            
            logger.info("Performance report analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze performance report: {e}")
            raise RuntimeError(f"Performance analysis failed: {e}")
    
    def _format_docs(self, docs: List[Document]) -> str:
        """
        Format retrieved documents for prompt context.
        """
        if not docs:
            return "No relevant context found."
        
        formatted = "\n\n".join([doc.page_content for doc in docs])
        return formatted
    



def get_qa_chain():
    """
    Fetch Q&A chain.
    """
    manager = PerformanceChainManager()
    return manager.get_qa_chain()


def get_summary_chain():
    """
    Fetch Summary chain.
    """
    manager = PerformanceChainManager()
    return manager.get_summary_chain()