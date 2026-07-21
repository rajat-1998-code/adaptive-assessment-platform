from pydantic import SecretStr
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


settings = Settings()
