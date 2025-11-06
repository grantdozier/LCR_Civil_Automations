"""
Configuration management for LCR Civil Drainage Automation System
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "LCR Civil Drainage Automation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/lcr_drainage"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # LangChain / OpenAI (for Module B)
    OPENAI_API_KEY: Optional[str] = None
    LANGCHAIN_TRACING_V2: bool = False

    # File paths
    PROJECT_CONTEXT_PATH: str = "/app/project_context"
    UPLOAD_DIR: str = "/app/uploads"
    OUTPUT_DIR: str = "/app/outputs"

    # Module A - Area Calculation
    AREA_CALCULATION_PRECISION: int = 2  # Decimal places
    C_VALUE_PRECISION: int = 3  # Decimal places for runoff coefficients

    # Module C - DIA Report
    RATIONAL_METHOD_ACCURACY: float = 0.02  # ±2% for Q=CiA
    TC_ACCURACY: float = 1.0  # ±1.0 minute for Time of Concentration

    # Module D - QA
    QA_PASS_THRESHOLD: float = 0.80  # 80% pass rate minimum

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
