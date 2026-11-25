from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sovela AI Core"
    VERSION: str = "0.1.0-alpha"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database & Cache
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./sovela_dev.db",
        description="Async PostgreSQL (production) or Async SQLite (development)"
    )
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # Security & CORS
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    JWT_SECRET_KEY: str = "sovela_jwt_secret_key_verified_development_environment_32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # AI Router Configuration
    AI_ROUTER_MODE: str = "simulation" # 'simulation' for deterministic offline/tests, 'live' for API keys
    LLM_TTFB_ABORT_THRESHOLD_MS: int = 200 # Time To First Byte (TTFB) abort threshold in ms
    
    # Canonical AI Provider Models (Verified Active Snapshots Only)
    # Audited Lifecycle Verification (November 2026):
    # - gpt-4o-mini-2024-07-18: ACTIVE OpenAI static snapshot ($0.150/$0.600 per 1M tokens)
    # - gemini-3.5-flash-lite: ACTIVE Google Gemini Flash successor (gemini-2.0-flash RETIRED June 1, 2026)
    # - claude-haiku-5-5: ACTIVE Anthropic Haiku successor (claude-3-5-haiku-20241022 RETIRED Feb 19, 2026)
    # - claude-sonnet-5-5: ACTIVE Anthropic Sonnet successor (claude-3-5-sonnet-20241022 RETIRED Oct 28, 2025)
    # - text-embedding-3-small: ACTIVE OpenAI embedding model (1536 dims)
    MODEL_TIER1_PRIMARY: str = "gpt-4o-mini-2024-07-18"
    MODEL_TIER1_FALLBACK: str = "gemini-3.5-flash-lite"
    MODEL_TIER2_SOCRATIC: str = "claude-haiku-5-5"
    MODEL_TIER3_COMPLEX: str = "claude-sonnet-5-5"
    MODEL_EMBEDDINGS: str = "text-embedding-3-small"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    
    # Governance & Product Owner Decisions (Pending PO Approval Flags)
    ENABLE_CLOUD_VOICE: bool = False       # DEC-01: Text-first V1 ($0.00 cloud compute)
    ENABLE_B2B_TENANCY: bool = False       # DEC-03: Multi-tenant ready schema, B2B gated
    REQUIRE_GUARDIAN_CONSENT: bool = False # DEC-05: Age-gate consent workflow
    ENABLE_LIVE_SCRAPING: bool = False     # DEC-06B: Opportunity hub scraping
    
    # Default Limits
    DAILY_CAPACITY_CAP_HOURS: float = 5.0
    PRO_DAILY_AI_LIMIT: int = 50
    FREE_DAILY_AI_LIMIT: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
