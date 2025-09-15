# 🚀 Log Analyzer & Performance Insights Platform  

A FastAPI-based system for **log ingestion, performance report generation, and AI-powered analysis** using LangChain & OpenAI.  

The platform enables teams to:  
- Upload test logs with file size in GBs (CSV/JSON)  
- Normalize & ingest into PostgreSQL with staging  
- Generate rich HTML performance reports with plots  
- Summarize & analyze results using LLMs (LangChain + OpenAI)  
- Ask natural language questions about performance metrics  

---

## ✨ Features  

✅ **File Upload & Ingestion**  
- Upload CSV/JSON logs
- Chunked ingestion pipeline with staging tables for atomicity and rollback safety
- Async ingestion powered by Celery + Redis, with job progress tracking 

✅ **Report Generation**  
- Compute global & endpoint metrics (p95 latency, throughput, error rates)
- Generate HTML reports with tables & plots  

✅ **LangChain Analysis**  
- Summarize reports into **executive summaries**  
- Detect anomalies in performance data  
- Generate **optimization recommendations**  
- Interactive Q&A on reports with retrieval-augmented generation (RAG)
- Async analysis generation and Q&A using Celery + Redis  

✅ **API Endpoints**  
- `/health/health_check` → System health check + celery health check
- `/health/celery` → celery health check
- `/upload` → Upload logs for ingestion and trigger celery job for async ingestion
- `/upload/jobs/{job_id}` → Check the status of a particular job id
- `/upload/file/{file_id}/jobs` → Get a list of all the celery jobs tied to a file id
- `/report/generate-eda-report` → Generate html report for uploaded file id  
- `/analyze/analyze-async` → Trigger celery job for OpenAI-powered report analysis
- `/analyze/ask-async` → Trigger celery job for asking performance-related questions 
- `/analyze/jobs/{job_id}` → Check the status and get the respose for analysis related celery jobs
- `/analyze/report/{report_id}/jobs` → Get all analysis type celery jobs for a specific report.

---

## 🛠️ Tech Stack  

- **Backend**: FastAPI  
- **Database**: PostgreSQL 
- **Data Processing**: Pandas  
- **Vector DB**: ChromaDB  
- **AI/LLM**: LangChain + OpenAI (Chat & Embeddings)  
- **Visualization**: Matplotlib for plots
- **Task Queue**: Celery + Redis (Docker)
- **Message Broker**: RabbitMQ (Docker) 

---

## Example Flow

1. Run any K6 test (can also run sample in K6_test/sample_k6_test.js) and get the output in JSON/CSV.
2. POST /upload :
    - upload raw output of k6 test using this endpoint to create ingestion job
    - Creates celery job to normalize raw data and begin data ingestion in PostgreSQL (staging table -> main table)
3. POST /upload/jobs/{job_id} :
    - Check the status of the ingestion celery job
4. POST /report/generate-eda-report :
    - Generate html report containing metrics and plots to be fed into langchain (check data/reports for sample)
5. POST /analyze/analyze-async :
    - Enter the report id in body to trigger celery job for the complete analysis of the report through langchain:
        - Endpoint analysis
        - Irregularities analysis
        - Capacity Assessment - Current throughput vs expected load
        - Error Rate Patterns
    ![Upload Example](sample_api_screenshots/full_analysis.jpg)
    ![Upload Example](sample_api_screenshots/full_analysis_response.jpg)
6. POST /analyze/ask-async :
    - Enter the report id and question in body to trigger celery job for asking question about the metrics
    ![Upload Example](sample_api_screenshots/qa_question.jpg)
    ![Upload Example](sample_api_screenshots/qa_response.jpg)
7. POST /analyze/jobs/{job_id} :
    - Check the status of the analysis or Q&A celery job


---

## Roadmap

1. LangChain Optimization
    - Integrate Redis caching for retriever objects to avoid repeated embedding overhead across Celery workers.
    - Persist Q&A and analysis responses tied to specific reports (report_id) to avoid repetition of openai analysis calls.
2. Database Partitioning
    - Implement timestamp based partitioning for the request_logs table.
3. Add simple UI (streamlit, gradio etc)
