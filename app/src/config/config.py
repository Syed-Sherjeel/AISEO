from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    db_path: str = "jobs.db"


settings = Settings()