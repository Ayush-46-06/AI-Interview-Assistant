from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Interview Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str

    # Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # External APIs
    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # Redis (Optional depending on usage, but keeping as string type)
    REDIS_URL: str = ""
    
    # STT Config
    STT_PROVIDER: str = "groq"
    STT_LANGUAGE: str = "en"
    
    # WebSocket Config
    WS_MAX_AUDIO_BYTES: int = 25 * 1024 * 1024 # 25MB max audio buffer

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
