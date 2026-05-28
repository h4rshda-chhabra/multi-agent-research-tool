import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables
from app.api.v1 import v1_router

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", env=settings.APP_ENV)
    await create_tables()
    
    # 1. Environment & Config Status Logging
    print("=" * 80, flush=True)
    print(" [STARTUP] AI Research Assistant Backend Startup Diagnostics", flush=True)
    print("=" * 80, flush=True)
    print(f" - Environment:    {settings.APP_ENV}", flush=True)
    print(f" - Database URL:  {settings.DATABASE_URL}", flush=True)
    print(f" - Frontend URL:  {settings.FRONTEND_URL}", flush=True)
    print("-" * 80, flush=True)

    # 2. Ensure authentication endpoints are tested during startup
    print(" [TEST] Running Authentication Subsystem Self-Tests...", flush=True)
    try:
        from app.api.v1.auth import _hash, _verify, _create_token
        from jose import jwt
        
        test_password = "startup-test-password-123"
        hashed = _hash(test_password)
        if not _verify(test_password, hashed):
            raise ValueError("Bcrypt verification failed")
            
        test_user_id = "test-user-id"
        token = _create_token(test_user_id)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("sub") != test_user_id:
            raise ValueError("JWT sub match failed")
            
        print(" [OK] Authentication self-tests: PASSED", flush=True)
    except Exception as e:
        print(f" [FAILED] Authentication self-tests: FAILED ({e})", flush=True)
        logger.error("Auth self-test failure", error=str(e))
    print("-" * 80, flush=True)

    # 3. Ensure the app fails gracefully if API keys are missing
    print(" [API KEYS] Verifying API Key Configurations...", flush=True)
    missing_keys = settings.missing_keys

    if missing_keys:
        print("+" + "="*78 + "+", flush=True)
        print("|" + " " * 31 + "CRITICAL WARNING" + " " * 31 + "|", flush=True)
        print("+" + "="*78 + "+", flush=True)
        print("| The following required API keys are missing from configuration:              |", flush=True)
        for key in missing_keys:
            key_line = f"|   - {key}"
            print(f"{key_line:<79}|", flush=True)
        print("|" + " " * 78 + "|", flush=True)
        print("| Please set them in your backend/.env file.                                   |", flush=True)
        print("| Without these keys, AI-powered agent research pipelines will fail.           |", flush=True)
        print("| The backend will continue to run to support health checks and auth.          |", flush=True)
        print("+" + "="*78 + "+", flush=True)
    else:
        print(" [OK] All critical API keys are loaded successfully.", flush=True)
    print("=" * 80, flush=True)

    yield
    logger.info("shutdown")


app = FastAPI(
    title="AI Research Assistant",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Standardize frontend origins for CORS configuration
allowed_origins = ["http://localhost:3001"]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in allowed_origins:
    allowed_origins.append(settings.FRONTEND_URL)

if not settings.is_production:
    for local_origin in ["http://localhost:3000", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]:
        if local_origin not in allowed_origins:
            allowed_origins.append(local_origin)

# Configure CORS middleware globally before defining routes
# Automatically include:
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

