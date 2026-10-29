import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "HostelFix API"
    api_prefix: str = "/api/v1"
    database_url: str = "mysql+pymysql://hostelfix:hostelfix_dev_password@db:3306/hostelfix?charset=utf8mb4"
    environment: str = "development"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    seed_on_startup: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
