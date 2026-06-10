from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    DATABASE_URL: str = "sqlite+aiosqlite:///./research.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalise_db_url(cls, v: str) -> str:
        # Render and most PaaS providers give postgresql:// or postgres://.
        # SQLAlchemy's async engine requires the +asyncpg dialect prefix.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    GEMINI_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:3001"
    # Comma-separated list of additional allowed CORS origins.
    # Use this on Render/Vercel to add production URLs without changing code:
    #   CORS_ORIGINS=https://your-app.vercel.app,https://custom-domain.com
    CORS_ORIGINS: str = ""

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def missing_keys(self) -> list[str]:
        missing = []
        if not self.GEMINI_API_KEY or self.GEMINI_API_KEY.startswith("AIza..."):
            missing.append("GEMINI_API_KEY")
        if not self.TAVILY_API_KEY or self.TAVILY_API_KEY.startswith("tvly-..."):
            missing.append("TAVILY_API_KEY")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()
