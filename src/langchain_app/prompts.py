from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any

from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger()


def get_qa_prompt() -> PromptTemplate:
    """
    Create Q&A prompt template for performance report analysis.
    """
    try:
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a senior performance engineer analyzing load test results. 
                        Use the performance report context below to answer the question with specific, actionable insights.

                        Performance Report Context:
                        {context}

                        Question: {question}

                        Instructions:
                        - Focus on performance metrics (response times, throughput, error rates)
                        - Identify specific bottlenecks and root causes
                        - Provide actionable recommendations with concrete steps
                        - Use actual numbers from the report when available
                        - If the context doesn't contain enough information, say so clearly

                        Answer:"""
            )
        
        logger.debug("Q&A prompt template created successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Failed to create Q&A prompt: {e}")
        raise RuntimeError(f"Q&A prompt creation failed: {e}")


def get_summary_prompt() -> PromptTemplate:
    """
    Create summary prompt template for executive performance summaries.
    """
    try:
        prompt = PromptTemplate(
            input_variables=["context"],
            template="""You are a senior performance architect creating an executive summary of load test results.

                        Performance Report Data:
                        {context}

                        Create a comprehensive executive summary that includes:

                        1. **Overall Performance Assessment**: Pass/Fail with key metrics
                        2. **Critical Issues**: Top 3 performance problems identified
                        3. **Endpoint Analysis**: Best and worst performing endpoints
                        4. **Capacity Assessment**: Current throughput vs expected load
                        5. **Immediate Actions**: Top 3 priority recommendations
                        6. **Business Impact**: How performance affects user experience

                        Format your summary with clear sections and bullet points. Use specific metrics from the report.
                        Focus on business impact rather than technical details.

                        Executive Summary:"""
            )
        
        logger.debug("Summary prompt template created successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Failed to create summary prompt: {e}")
        raise RuntimeError(f"Summary prompt creation failed: {e}")


def get_anomaly_detection_prompt() -> PromptTemplate:
    """
    Create prompt for anomaly detection in performance data.
    """
    try:
        prompt = PromptTemplate(
            input_variables=["context"],
            template="""You are a performance monitoring specialist analyzing test results for anomalies.

                        Performance Data:
                        {context}

                        Analyze the data for anomalies and unusual patterns:

                        1. **Response Time Anomalies**: Unusual spikes or degradations
                        2. **Error Rate Patterns**: Sudden increases in specific status codes
                        3. **Throughput Irregularities**: Unexpected drops in RPS
                        4. **Endpoint Outliers**: Endpoints behaving differently than expected
                        5. **Trend Analysis**: Performance changes over time

                        For each anomaly found:
                        - Describe the specific pattern
                        - Estimate severity (Low/Medium/High)
                        - Suggest potential root causes
                        - Recommend investigation steps

                        If no significant anomalies are found, confirm that performance is stable.

                        Anomaly Analysis:"""
            )
        
        logger.debug("Anomaly detection prompt created successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Failed to create anomaly detection prompt: {e}")
        raise RuntimeError(f"Anomaly detection prompt creation failed: {e}")


def get_optimization_prompt() -> PromptTemplate:
    """
    Create prompt for optimization recommendations.
    """
    try:
        prompt = PromptTemplate(
            input_variables=["context", "sla_requirements"],
            template="""You are a performance optimization consultant analyzing load test results.

                        Performance Report:
                        {context}

                        SLA Requirements:
                        {sla_requirements}

                        Provide detailed optimization recommendations:

                        1. **Infrastructure Optimizations**:
                        - Server scaling recommendations
                        - Database optimization suggestions
                        - Caching strategies

                        2. **Application Optimizations**:
                        - Code-level improvements
                        - Query optimizations  
                        - Resource usage improvements

                        3. **Architecture Improvements**:
                        - Load balancing adjustments
                        - Service distribution changes
                        - Monitoring enhancements

                        4. **Priority Matrix**:
                        - High Impact / Low Effort (Quick wins)
                        - High Impact / High Effort (Strategic improvements)
                        - Expected performance improvements for each recommendation

                        Format recommendations with:
                        - Specific action items
                        - Expected impact metrics
                        - Implementation complexity (Low/Medium/High)
                        - Timeline estimates

                        Optimization Recommendations:"""
            )
        
        logger.debug("Optimization prompt created successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Failed to create optimization prompt: {e}")
        raise RuntimeError(f"Optimization prompt creation failed: {e}")


def validate_prompt_inputs(prompt_inputs: Dict[str, Any], required_vars: list) -> None:
    """
    Validate that all required prompt variables are provided.
    """
    missing_vars = []
    empty_vars = []
    
    for var in required_vars:
        if var not in prompt_inputs:
            missing_vars.append(var)
        elif not prompt_inputs[var] or (isinstance(prompt_inputs[var], str) and not prompt_inputs[var].strip()):
            empty_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required prompt variables: {missing_vars}")
    
    if empty_vars:
        raise ValueError(f"Empty prompt variables: {empty_vars}")
    
    logger.debug(f"Prompt validation passed for variables: {required_vars}")
