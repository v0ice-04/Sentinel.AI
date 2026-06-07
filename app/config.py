from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    hindsight_base_url: str = "http://localhost:8888"
    hindsight_api_key: str = ""
    groq_api_key: str
    bank_id: str = "devops-agent"
    groq_model: str = "llama3-8b-8192"
    recall_max_tokens: int = 4096
    recall_budget: str = "mid"
    groq_max_tokens: int = 1000
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
