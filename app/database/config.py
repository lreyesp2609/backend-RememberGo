from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración central de la aplicación.
    Los valores se cargan automáticamente desde variables de entorno o archivo .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_ignore_empty=True,
    )

    # ─── Aplicación ───────────────────────────────────────────────
    app_name: str = Field(default="Mi API Backend")
    debug: bool = Field(default=False)

    # ─── Base de datos ────────────────────────────────────────────
    db_user: str
    db_password: str
    db_host: str
    db_port: int = Field(default=6543)
    db_name: str = Field(default="postgres")

    # ─── Seguridad ────────────────────────────────────────────────
    secret_key: str = Field(min_length=32)
    algorithm: str = Field(
        default="HS256",
        pattern="^(HS256|HS384|HS512|RS256)$",
    )
    access_token_expire_minutes: int = Field(default=15)

    # ─── Admin inicial (seed) ─────────────────────────────────────
    admin_email: str = Field(default="admin@example.com")
    admin_password: str = Field(default="changeme123", min_length=8)

    # ─── API ──────────────────────────────────────────────────────
    api_base_url: str = Field(default="http://localhost:8000")

    # ─── URL de conexión (calculada, no expuesta en repr) ─────────
    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()