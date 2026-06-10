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

# ── CORS ────────────────────────────────────────────────────────────────────
#
# Starlette's CORSMiddleware supports allow_origin_regex.  When an origin
# matches via regex the middleware echoes back that *specific* origin (not
# "*"), which keeps allow_credentials=True valid per the CORS spec.
#
# Two-layer strategy:
#   1. Explicit list  – localhost always included; FRONTEND_URL / CORS_ORIGINS
#                       from env vars for any named production/custom domains.
#   2. Regex pattern  – matches every *.vercel.app URL (production + previews)
#                       so no env-var change is needed per Vercel deployment.

# Layer 1 – explicit origins
_explicit_origins: set[str] = {
    # Local development — always permitted regardless of APP_ENV
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
}

# Primary deployed frontend (set FRONTEND_URL on the Render dashboard)
if settings.FRONTEND_URL:
    _explicit_origins.add(settings.FRONTEND_URL.rstrip("/"))

# Optional extra origins: comma-separated for custom domains / staging URLs
if settings.CORS_ORIGINS:
    for _o in settings.CORS_ORIGINS.split(","):
        _o = _o.strip().rstrip("/")
        if _o:
            _explicit_origins.add(_o)

allowed_origins: list[str] = sorted(_explicit_origins)

# Layer 2 – regex for *.vercel.app (production + every preview deployment)
# re.fullmatch() is used internally, so the pattern must match the whole origin.
_VERCEL_ORIGIN_RE = r"https://[a-zA-Z0-9][a-zA-Z0-9\-]*\.vercel\.app"

# ── Startup logging (visible in Render / Docker logs) ───────────────────────
print("=" * 60, flush=True)
print("[CORS] Explicit allowed origins:", flush=True)
for _origin in allowed_origins:
    print(f"  {_origin}", flush=True)
print(f"[CORS] Origin regex pattern:  {_VERCEL_ORIGIN_RE}", flush=True)
print("=" * 60, flush=True)

# ── Register CORSMiddleware BEFORE routers ───────────────────────────────────
# app.add_middleware() wraps in LIFO order.  With only this one middleware
# call before include_router(), CORSMiddleware is the outermost layer and
# therefore intercepts every OPTIONS preflight before auth / routing runs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=_VERCEL_ORIGIN_RE,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(v1_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

