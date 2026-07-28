from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide configuration.

    Values are loaded from environment variables (or a .env file in local
    development). Add new settings here as the application needs them —
    do not hardcode config values elsewhere in the codebase.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Application ---
    APP_NAME: str = "Adaptive Assessment Platform"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- API ---
    API_V1_PREFIX: str = "/api/v1"

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Frontend ---
    FRONTEND_BASE_URL: str = "http://localhost:3000"

    # --- Authentication ---
    AUTH_ENABLED: bool = True
    AUTH_PREFIX: str = "/auth"
    AUTH_COOKIE_DOMAIN: str | None = None
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    AUTH_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_OTP_EXPIRE_MINUTES: int = 10
    AUTH_MAGIC_LINK_EXPIRE_MINUTES: int = 15
    AUTH_JWT_ALGORITHM: str = "HS256"
    AUTH_JWT_SECRET_KEY: SecretStr = SecretStr(
        "change-me-with-at-least-32-characters-for-development"
    )
    AUTH_ISSUER: str = "adaptive-assessment-platform"
    AUTH_AUDIENCE: str = "adaptive-assessment-users"

    # --- Guest sessions ---
    GUEST_SESSION_EXPIRE_DAYS: int = 7

    # --- Email ---
    EMAILS_ENABLED: bool = True
    EMAIL_FROM_NAME: str = "Adaptive Assessment Platform"
    EMAIL_FROM_ADDRESS: str = "noreply@localhost"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    SMTP_USE_TLS: bool = False
    SMTP_USE_STARTTLS: bool = False
    MAILHOG_UI_URL: str = "http://localhost:8025"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_value(cls, value: object) -> object:
        """
        Accept conventional booleans plus environment-style values such as
        "release" and "production" that may be injected by shells or IDEs.
        """

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True

            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False

        return value

    # --- PostgreSQL ---
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str = "adaptive_assessment"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def EMAIL_TEMPLATE_DIR(self) -> Path:
        return Path(__file__).resolve().parents[1] / "services" / "email" / "templates"


settings = Settings()
