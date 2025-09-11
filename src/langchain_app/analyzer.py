import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
from langchain_core.output_parsers import StrOutputParser

from src.langchain_app.chains import PerformanceChainManager
from src.langchain_app.retriever import ReportRetriever
from src.langchain_app.prompts import (
    get_qa_prompt, 
    get_summary_prompt, 
    get_anomaly_detection_prompt,
    get_optimization_prompt,
    validate_prompt_inputs
)

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()


class PerformanceAnalyzer:
    def __init__(self):
        """
        Initialize the performance analyzer.
        """
        self.chain_manager = PerformanceChainManager()
        self.retriever_manager = ReportRetriever()
        
        # Cache for analysis results
        self._last_analysis = None
        self._last_report_hash = None
        
        logger.info("PerformanceAnalyzer initialized successfully")

    def analyze_report_from_name(self, report_name: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a specific performance report.
        """
        try:
            report_path = Path(settings.REPORTS_DIR) / (report_name if report_name.endswith(".html") else f"{report_name}.html")
            if not report_path.exists():
                logger.error(f"Report not found: {report_path}")
                raise FileNotFoundError(f"Report not found: {report_path}")
            return self.perform_report_analysis(report_name)
        except Exception as e:
            logger.error(f"Failed to analyze specific performance report: {e}")
            raise RuntimeError(f"Performance analysis failed: {e}")

    def analyze_latest_report(self) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of the latest performance report.
        """
        try:
            logger.info("Starting comprehensive performance report analysis")
            
            report_name = self.retriever_manager.load_latest_report()
            return self.perform_report_analysis(report_name)
        except Exception as e:
            logger.error(f"Failed to analyze latest performance report: {e}")
            raise RuntimeError(f"Performance analysis failed: {e}")
    
    def perform_report_analysis(self, report_name: str) -> Dict[str, Any]:
        """
        Fetch executive summary, insights, anolmalies and recommendatoins for the performance report.
        """
        try:
            logger.info("Starting comprehensive performance report analysis")
            report_path = Path(settings.REPORTS_DIR) / (report_name if report_name.endswith(".html") else f"{report_name}.html")
            report_content = report_path.read_text(encoding="utf-8")
            
            report_hash = hash(report_name)
            
            if self._last_report_hash == report_hash and self._last_analysis:
                logger.info("Using cached analysis results")
                return self._last_analysis
            
            analysis_results = {
                "executive_summary": self._generate_executive_summary(report_name),
                "anomaly_detection": self._detect_anomalies(report_name), 
                "optimization_recommendations": self._generate_optimizations(report_name),
                "qa_insights": self._generate_qa_insights(report_name),
                "metadata": {
                    "analysis_timestamp": pd.Timestamp.now().isoformat(),
                    "report_length_chars": len(report_content),
                    "llm_model": settings.LLM_MODEL,
                    "embeddings_model": settings.EMBEDDINGS_MODEL
                }
            }
            
            self._last_analysis = analysis_results
            self._last_report_hash = report_hash
            
            logger.info("Performance report analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Failed to analyze performance report: {e}")
            raise RuntimeError(f"Performance analysis failed: {e}")
    
    def generate_executive_summary(self, report_name: Optional[str] = None) -> str:
        """
        Generate executive summary of performance results.
        """
        try:
            content = report_name or self.retriever_manager.load_latest_report()
            
            return self._generate_executive_summary(content)
            
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            raise
    
    def answer_question(self, question: str, report_name: Optional[str] = None) -> str:
        """
        Answer specific questions about performance report.
        """
        try:
            validate_prompt_inputs({"question": question}, ["question"])
            retriever = self.retriever_manager.build_retriever(report_name or self.retriever_manager.load_latest_report())
            
            qa_chain = self.chain_manager.get_qa_chain(retriever)
            answer = qa_chain.invoke(question)
            
            logger.info(f"Successfully answered question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            raise
    
    def detect_anomalies(self, report_name: Optional[str] = None) -> str:
        """
        Detect performance anomalies in the report.
        """
        try:
            content = report_name or self.retriever_manager.load_latest_report()
            return self._detect_anomalies(content)
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise
    
    def generate_optimizations(self, report_name: Optional[str] = None, sla_requirements: str = "Standard web application SLAs") -> str:
        """
        Generate optimization recommendations.
        """
        try:
            content = report_name or self.retriever_manager.load_latest_report()
            return self._generate_optimizations(content, sla_requirements)
            
        except Exception as e:
            logger.error(f"Failed to generate optimizations: {e}")
            raise
    
    def _generate_executive_summary(self, report_name: str) -> str:
        """
        Generate executive summary using summary chain with chunking for large reports.
        """
        try:
            retriever = self.retriever_manager.build_retriever(report_name)
            summary_chain = self.chain_manager.get_summary_chain(retriever)
            return summary_chain.invoke("Summarize this report")
                
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            return f"Executive summary unavailable: {str(e)}"
    
    def _detect_anomalies(self, report_name: str) -> str:
        """
        Detect anomalies using anomaly detection prompt.
        """
        try:
            anomaly_prompt = get_anomaly_detection_prompt()
            retriever = self.retriever_manager.build_retriever(report_name)
            anomaly_chain = (
                {"context": retriever | self.chain_manager._format_docs}
                | anomaly_prompt
                | self.chain_manager.llm
                | StrOutputParser())
            return anomaly_chain.invoke("Detect anomalies in this report")
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return f"Anomaly detection unavailable: {str(e)}"
    
    def _generate_optimizations(self, report_name: str, sla_requirements: str = "Standard SLAs") -> str:
        """
        Generate optimization recommendations.
        """
        try:
            optimization_prompt = get_optimization_prompt()
            retriever = self.retriever_manager.build_retriever(report_name)
            optimization_chain = (
                {"context": retriever | self.chain_manager._format_docs}
                | optimization_prompt
                | self.chain_manager.llm
                | StrOutputParser())
            return optimization_chain.invoke(sla_requirements)
        except Exception as e:
            logger.error(f"Optimization generation failed: {e}")
            return f"Optimization recommendations unavailable: {str(e)}"
    
    def _generate_qa_insights(self, report_name: str) -> Dict[str, str]:
        """
        Generate insights using predefined questions.
        """
        retriever = self.retriever_manager.build_retriever(report_name)
        qa_chain = self.chain_manager.get_qa_chain(retriever)
        
        key_questions = [
            "What are the main performance bottlenecks identified?",
            "Which endpoints have the highest error rates?",
            "What is the overall system performance assessment?", 
            "What are the recommended optimizations?",
            "How does the current performance compare to typical benchmarks?"
        ]
        
        insights = {}
        for question in key_questions:
            try:
                answer = qa_chain.invoke(question)
                insights[question] = answer
            except Exception as e:
                logger.warning(f"Failed to answer question '{question}': {e}")
                insights[question] = f"Analysis unavailable: {str(e)}"
        
        return "\n\n".join(f"Q: {q}\nA: {a}" for q, a in insights.items())
    


# Convenience functions for simple use cases
def analyze_latest_report() -> Dict[str, Any]:
    """
    Analyze the latest performance report.
    """
    analyzer = PerformanceAnalyzer()
    try:
        return analyzer.analyze_latest_report()
    finally:
        logger.info("PerformanceAnalyzer completed")


def generate_quick_summary(report_name: Optional[str] = None) -> str:
    """
    Generate a quick executive summary.
    """
    analyzer = PerformanceAnalyzer()
    try:
        return analyzer.generate_executive_summary(report_name)
    finally:
        logger.info("PerformanceAnalyzer completed")
