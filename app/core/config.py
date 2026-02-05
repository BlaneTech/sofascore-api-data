
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    
    DATABASE_URL: str = "postgresql+asyncpg://football_user:password@localhost:5432/football_db"
    
    # API Sofascore
    # SOFASCORE_BASE_URL: str = "https://api.sofascore.com/api/v1"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Application
    APP_NAME: str = "GOGAinde-Data"
    APP_VERSION: str = "1.0.0"
    APP_PORT: int = 8000 
    REDIS_URL: str = "redis://localhost:6379/0" 
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Instance globale
settings = Settings()
