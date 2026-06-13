from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "CineGen AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Supabase / Database
    SUPABASE_URL: str = "https://mvrrthyekctgwqtabold.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_URL: str = ""

    # Anthropic (Script Intelligence)
    ANTHROPIC_API_KEY: str = ""

    # Video Generation
    KLING_API_KEY: str = ""
    RUNWAY_API_KEY: str = ""

    # Audio
    ELEVENLABS_API_KEY: str = ""
    SUNO_API_KEY: str = ""
    SYNCSO_API_KEY: str = ""

    # Storage
    CLOUDFLARE_R2_ACCESS_KEY: str = ""
    CLOUDFLARE_R2_SECRET_KEY: str = ""
    CLOUDFLARE_R2_BUCKET: str = "cinegen-media"
    CLOUDFLARE_R2_ENDPOINT: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # JWT
    SECRET_KEY: str = "cinegen-dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
