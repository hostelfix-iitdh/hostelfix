from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HostelFix API"
    api_prefix: str = "/api/v1"
    database_url: str = (
        "mysql+pymysql://hostelfix:hostelfix_dev_password@db:3306/hostelfix?charset=utf8mb4"
    )
    environment: str = "development"
    cors_origins: str = "http://localhost:8080,http://localhost:5173,http://localhost:3000"
    seed_on_startup: bool = True
    session_secret: str = "CHANGE_ME_SESSION_SECRET_32_CHARS_MINIMUM"
    session_hours: int = 24
    google_client_id: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    ai_timeout_seconds: int = 30
    ai_max_chars: int = 500
    ai_max_image_bytes: int = 5 * 1024 * 1024
    ai_daily_limit: int = 1
    cookie_secure: bool = False
    mail_mode: str = "log"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
