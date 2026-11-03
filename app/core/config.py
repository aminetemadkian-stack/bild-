from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ArchAI Multi-Agent Starter"
    database_path: str = "./data/archai.db"
    host: str = "127.0.0.1"
    port: int = 8000
    llm_provider: str = "demo"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 90
    chat_history_enabled: bool = False
    chat_history_retention_days: int = 30
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
