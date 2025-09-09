
import os
from pathlib import Path
from dotenv import load_dotenv
# from fix_imports import *

# Debug environment loading
# env_path = os.path.join(Path(__file__).parent.parent, ".envs", ".env.local")
# print(f"Looking for .env file at: {env_path}")
# print(f"File exists: {os.path.exists(env_path)}")

# # Let's also check what's in the .envs directory
# envs_dir = os.path.join(Path(__file__).parent.parent, ".envs")
# print(f"Contents of .envs directory: {os.listdir(envs_dir)}")

# # Try loading environment
# loaded = load_dotenv(env_path)
# print(f"Environment loaded successfully: {loaded}")

# # Check if OPENAI_API_KEY is now available
# api_key = os.getenv("OPENAI_API_KEY")
# print(f"OPENAI_API_KEY found: {'Yes' if api_key else 'No'}")
# if api_key:
#     print(f"API key starts with: {api_key[:10]}...")

# print("Environment variables loaded, importing analyzer...")

from src.langchain_app.analyzer import PerformanceAnalyzer, generate_quick_summary

analyzer = PerformanceAnalyzer()
# results = analyzer.analyze_latest_report()
# results = generate_quick_summary()
results = analyzer.answer_question("What is the average response time for the application?")

# Advanced usage with custom settings:
# from src.langchain_app.config import LangChainSettings

# custom_settings = LangChainSettings(llm_model="gpt-3.5-turbo")
# analyzer = PerformanceAnalyzer(custom_settings)
# summary = analyzer.generate_executive_summary()
print(results)
