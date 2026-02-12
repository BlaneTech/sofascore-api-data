
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    
    DATABASE_URL: str = "postgresql+asyncpg://football_user:password@localhost:5432/football_db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Application
    APP_NAME: str = "gogainde-data"
    APP_VERSION: str = "1.0.0"
    APP_PORT: int = 8000 
    REDIS_URL: str = "redis://localhost:6379/0" 
    APP_ENV: str = "development"
    ADMIN_SECRET: str = "goga_XsrHl4G2f6nCE1gfRGTiMfUf1ECYS00AiX6a"

    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Instance globale
settings = Settings()
