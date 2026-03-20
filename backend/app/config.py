"""Minimal pydantic settings — only DB creds, log level, and CORS origins from .env.
All runtime settings are stored in the system_settings DB table."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "mariadb"
    db_port: int = 3306
    db_user: str = "gridmind"
    db_password: str = ""
    db_name: str = "gridmind"
    log_level: str = "INFO"
    # Comma-separated list of allowed CORS origins.
    # Set to "*" for development (default). In production, set to the frontend URL.
    # Example: CORS_ORIGINS=http://192.168.1.76:3009
    cors_origins: str = "*"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
