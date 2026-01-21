from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_port: int = 8000
    database_url: str = "postgresql+asyncpg://football_user:password@localhost:5432/football_db"
    redis_url: str = "redis://localhost:6379/0"
    sofa_cache_ttl: int = 300
    rate_limit_per_minute: int = 60
    admin_api_key: str = "change-this-key"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
