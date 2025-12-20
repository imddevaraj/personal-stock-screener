"""
Configuration management using Pydantic Settings v2.
All configuration is loaded from environment variables for security.
"""
import os
from typing import Any, Dict, List, Optional
from pydantic import field_validator, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and type safety."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application Info
    APP_NAME: str = "Personal Stock Screener"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    
    # Database Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        """Build database URL from components if not provided."""
        if isinstance(v, str) and v:
            return v
        values = info.data
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info) -> str:
        """Build Redis URL from components if not provided."""
        if isinstance(v, str) and v:
            return v
        values = info.data
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Data Source API Keys
    MARKET_DATA_API_KEY: Optional[str] = None
    MARKET_DATA_BASE_URL: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # Scoring Configuration
    FUNDAMENTAL_WEIGHT: float = Field(default=0.6, ge=0, le=1)
    SENTIMENT_WEIGHT: float = Field(default=0.4, ge=0, le=1)
    
    @field_validator("SENTIMENT_WEIGHT")
    @classmethod
    def weights_must_sum_to_one(cls, v: float, info) -> float:
        """Ensure fundamental and sentiment weights sum to 1."""
        values = info.data
        fundamental_weight = values.get("FUNDAMENTAL_WEIGHT", 0.6)
        total = fundamental_weight + v
        if abs(total - 1.0) > 0.01:  # Allow small floating point error
            raise ValueError(
                f"FUNDAMENTAL_WEIGHT ({fundamental_weight}) + "
                f"SENTIMENT_WEIGHT ({v}) must equal 1.0, got {total}"
            )
        return v
    
    # Fundamental Scoring Thresholds
    PE_RATIO_EXCELLENT: float = 15.0
    PE_RATIO_GOOD: float = 25.0
    PB_RATIO_EXCELLENT: float = 2.0
    PB_RATIO_GOOD: float = 3.0
    ROE_EXCELLENT: float = 20.0
    ROE_GOOD: float = 15.0
    DEBT_TO_EQUITY_EXCELLENT: float = 0.5
    DEBT_TO_EQUITY_GOOD: float = 1.0
    
    # Sentiment Analysis
    SENTIMENT_MODEL: str = "ProsusAI/finbert"
    SENTIMENT_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Celery Configuration
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    CELERY_TASK_ALWAYS_EAGER: bool = False
    
    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def set_celery_broker(cls, v: Optional[str], info) -> str:
        """Use Redis URL for Celery broker if not specified."""
        if v:
            return v
        values = info.data
        return values.get("REDIS_URL") or ""
    
    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def set_celery_backend(cls, v: Optional[str], info) -> str:
        """Use Redis URL for Celery result backend if not specified."""
        if v:
            return v
        values = info.data
        return values.get("REDIS_URL") or ""
    
    # Ingestion Schedules (Cron format)
    FUNDAMENTAL_INGESTION_CRON: str = "0 17 * * 1-5"  # Daily at 5 PM IST (weekdays)
    NEWS_INGESTION_CRON: str = "0 */2 * * *"          # Every 2 hours
    SCORING_CRON: str = "0 18 * * 1-5"                # Daily at 6 PM IST
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_TRACING: bool = False
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831
    
    # Stock Universe
    TRACKED_STOCKS: str = Field(
        default="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK,BHARTIARTL,ITC,SBIN,LT,HINDUNILVR"
    )
    
    def get_tracked_stocks_list(self) -> List[str]:
        """Get tracked stocks as a list."""
        if isinstance(self.TRACKED_STOCKS, str):
            return [s.strip().upper() for s in self.TRACKED_STOCKS.split(",") if s.strip()]
        return self.TRACKED_STOCKS


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.
    
    This function is useful for dependency injection in FastAPI.
    
    Returns:
        Settings instance
    """
    return settings
