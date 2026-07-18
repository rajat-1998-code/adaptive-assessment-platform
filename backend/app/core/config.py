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


settings = Settings()