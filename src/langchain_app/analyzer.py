import pandas as pd
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from bs4 import BeautifulSoup
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
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """
        Extract meaningful text from HTML report using bs4.
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            logger.debug(f"HTML content reduced from {len(html_content)} to {len(text)} characters")
            return text
                
        except Exception as e:
            logger.warning(f"HTML text extraction failed: {e}. Using original content.")
            return html_content

    def analyze_report_from_name(self, report_name: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a specific performance report.
        """
        try:
            report_content = self.retriever_manager.load_specific_report(report_name)
            return self.perform_report_analysis(report_content)
        except Exception as e:
            logger.error(f"Failed to analyze specific performance report: {e}")
            raise RuntimeError(f"Performance analysis failed: {e}")

    def analyze_latest_report(self) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of the latest performance report.
        """
        try:
            logger.info("Starting comprehensive performance report analysis")
            
            report_content = self.retriever_manager.load_latest_report()
            return self.perform_report_analysis(report_content)
        except Exception as e:
            logger.error(f"Failed to analyze latest performance report: {e}")
            raise RuntimeError(f"Performance analysis failed: {e}")
    
    def perform_report_analysis(self, report_content: str) -> Dict[str, Any]:
        """
        Fetch executive summary, insights, anolmalies and recommendatoins for the performance report.
        """
        try:
            logger.info("Starting comprehensive performance report analysis")
            
            report_hash = hash(report_content)
            
            if self._last_report_hash == report_hash and self._last_analysis:
                logger.info("Using cached analysis results")
                return self._last_analysis
            
            analysis_results = {
                "executive_summary": self._generate_executive_summary(report_content),
                "anomaly_detection": self._detect_anomalies(report_content), 
                "optimization_recommendations": self._generate_optimizations(report_content),
                "qa_insights": self._generate_qa_insights(report_content),
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
    
    def generate_executive_summary(self, report_content: Optional[str] = None) -> str:
        """
        Generate executive summary of performance results.
        """
        try:
            content = report_content or self.retriever_manager.load_latest_report()
            
            # Extract text from HTML to reduce token count
            if content.strip().startswith('<!DOCTYPE html') or content.strip().startswith('<html'):
                logger.info("HTML report detected, extracting text content")
                content = self._extract_text_from_html(content)
            
            return self._generate_executive_summary(content)
            
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            raise
    
    def answer_question(self, question: str, report_content: Optional[str] = None) -> str:
        """
        Answer specific questions about performance report.
        """
        try:
            validate_prompt_inputs({"question": question}, ["question"])
            if report_content:
                self.retriever_manager.update_vectorstore(report_content)
            
            qa_chain = self.chain_manager.get_qa_chain()
            answer = qa_chain.invoke(question)
            
            logger.info(f"Successfully answered question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            raise
    
    def detect_anomalies(self, report_content: Optional[str] = None) -> str:
        """
        Detect performance anomalies in the report.
        """
        try:
            content = report_content or self.retriever_manager.load_latest_report()
            return self._detect_anomalies(content)
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise
    
    def generate_optimizations(self, report_content: Optional[str] = None, sla_requirements: str = "Standard web application SLAs") -> str:
        """
        Generate optimization recommendations.
        """
        try:
            content = report_content or self.retriever_manager.load_latest_report()
            return self._generate_optimizations(content, sla_requirements)
            
        except Exception as e:
            logger.error(f"Failed to generate optimizations: {e}")
            raise
    
    def _generate_executive_summary(self, report_content: str) -> str:
        """
        Generate executive summary using summary chain with chunking for large reports.
        """
        try:
            estimated_tokens = len(report_content) / 4
            
            if estimated_tokens > 15000:
                logger.info(f"Large report detected ({estimated_tokens:.0f} tokens). Using chunked summarization.")
                return self._generate_chunked_summary(report_content)
            else:
                summary_chain = self.chain_manager.get_summary_chain()
                return summary_chain.invoke({"context": report_content})
                
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            return self._generate_chunked_summary(report_content)
    
    def _generate_chunked_summary(self, report_content: str) -> str:
        """
        Generate summary using retrieval-based chunking for large reports.
        """
        try:
            self.retriever_manager.update_vectorstore(report_content)
            
            qa_chain = self.chain_manager.get_qa_chain()
            
            summary_questions = [
                "What are the overall performance results and key metrics?",
                "What are the main performance issues and bottlenecks?", 
                "Which endpoints performed best and worst?",
                "What are the critical recommendations for improvement?"
            ]
            
            insights = []
            for question in summary_questions:
                try:
                    answer = qa_chain.invoke(question)
                    insights.append(f"**{question}**\n{answer}")
                except Exception as e:
                    logger.warning(f"Failed to answer summary question: {e}")
                    insights.append(f"**{question}**\nAnalysis unavailable: {str(e)}")
            
            summary = "# Executive Performance Summary\n\n" + "\n\n".join(insights)
            
            logger.info("Chunked executive summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Chunked summary generation failed: {e}")
            return f"Executive summary unavailable due to report size constraints. Error: {str(e)}"
    
    def _detect_anomalies(self, report_content: str) -> str:
        """
        Detect anomalies using anomaly detection prompt.
        """
        try:
            anomaly_prompt = get_anomaly_detection_prompt()
            anomaly_chain = anomaly_prompt | self.chain_manager.llm | StrOutputParser()
            return anomaly_chain.invoke({"context": report_content})
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return f"Anomaly detection unavailable: {str(e)}"
    
    def _generate_optimizations(self, report_content: str, sla_requirements: str = "Standard SLAs") -> str:
        """
        Generate optimization recommendations.
        """
        try:
            optimization_prompt = get_optimization_prompt()
            optimization_chain = optimization_prompt | self.chain_manager.llm | StrOutputParser()
            return optimization_chain.invoke({
                "context": report_content,
                "sla_requirements": sla_requirements
            })
        except Exception as e:
            logger.error(f"Optimization generation failed: {e}")
            return f"Optimization recommendations unavailable: {str(e)}"
    
    def _generate_qa_insights(self, report_content: str) -> Dict[str, str]:
        """
        Generate insights using predefined questions.
        """
        qa_chain = self.chain_manager.get_qa_chain()
        
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
        
        return insights
    


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


def generate_quick_summary(report_content: Optional[str] = None) -> str:
    """
    Generate a quick executive summary.
    """
    analyzer = PerformanceAnalyzer()
    try:
        return analyzer.generate_executive_summary(report_content)
    finally:
        logger.info("PerformanceAnalyzer completed")
