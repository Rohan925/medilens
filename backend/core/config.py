# backend/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    """
    Global configuration class.

    This class ONLY stores configuration values.
    No business logic should live here.
    """
    APP_NAME = "MediLens"
    VERSION = "1.0.0"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"

    
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "dummy")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    
    OPENFDA_BASE_URL: str = os.getenv(
        "OPENFDA_BASE_URL",
        "https://api.fda.gov/drug/label.json"
    )
    OPENFDA_API_KEY: str | None = os.getenv("OPENFDA_API_KEY")

    
    MAX_CONTEXT_CHARS: int = int(os.getenv("MAX_CONTEXT_CHARS", "3000"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))

    
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_DIR: str = os.getenv("CACHE_DIR", "backend/data/cache")

    
    ENABLE_FACT_CHECKER: bool = True
    ENABLE_CITATIONS: bool = True
    ENABLE_SUMMARISER: bool = True
settings = Config()