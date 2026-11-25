from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.session import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.goals import router as goals_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.temporal import router as temporal_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.learning import router as learning_router
from app.db.seed_learning import seed_learning_data
from app.db.session import AsyncSessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    try:
        async with AsyncSessionLocal() as db:
            await seed_learning_data(db)
    except Exception as e:
        print(f"Warning: Failed to seed initial learning data: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Universal AI Life Operating System Core Monolith",
    lifespan=lifespan
)

# Finding 6: Secure CORS configuration - Never use wildcard "*" with allow_credentials=True
allowed_origins = [orig.strip() for orig in settings.CORS_ALLOWED_ORIGINS.split(",") if orig.strip()]
if not allowed_origins:
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Register REST Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(goals_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(temporal_router, prefix="/api/v1")
app.include_router(opportunities_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(learning_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "cors_origins": allowed_origins,
        "active_models": {
            "tier1_primary": settings.MODEL_TIER1_PRIMARY,
            "tier1_fallback": settings.MODEL_TIER1_FALLBACK,
            "tier2_socratic": settings.MODEL_TIER2_SOCRATIC,
            "tier3_complex": settings.MODEL_TIER3_COMPLEX,
            "embeddings": settings.MODEL_EMBEDDINGS
        },
        "abort_threshold_ms": settings.LLM_TTFB_ABORT_THRESHOLD_MS,
        "governance": {
            "dec_06a_opportunity_hub": "LOCKED_APPROVED",
            "dec_01_cloud_voice": settings.ENABLE_CLOUD_VOICE,
            "dec_03_b2b_tenancy": settings.ENABLE_B2B_TENANCY,
            "dec_05_guardian_consent": settings.REQUIRE_GUARDIAN_CONSENT
        }
    }
