from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """アプリケーション設定"""

    # Database
    database_url: str

    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    # Application
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

settings = Settings()
