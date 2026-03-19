"""Minimal pydantic settings — only DB creds and log level from .env.
All runtime settings are stored in the system_settings DB table."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "mariadb"
    db_port: int = 3306
    db_user: str = "gridmind"
    db_password: str = ""
    db_name: str = "gridmind"
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
