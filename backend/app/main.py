"""
ThreatScan — FastAPI Application Entry Point.

Production-grade malware analysis and threat intelligence platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import init_db
from app.logging import get_logger, setup_logging
from app.routes import admin, indicators, jobs, report, search, upload
from app.schemas.api import HealthResponse

settings = get_settings()
setup_logging(debug=settings.debug)
logger = get_logger(__name__)


# ── Rate Limiter ──
limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    logger.info("Starting ThreatScan API", environment=settings.environment)
    await init_db()
    yield
    logger.info("Shutting down ThreatScan API")


# ── Application ──
app = FastAPI(
    title="ThreatScan",
    description="Open-source malware analysis and threat intelligence platform",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ──
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """Returns service health status."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        services={
            "api": "running",
            "database": "connected",
        },
    )


# ── Register Routers ──
app.include_router(upload.router, tags=["upload"])
app.include_router(report.router, tags=["report"])
app.include_router(search.router, tags=["search"])
app.include_router(jobs.router, tags=["jobs"])
app.include_router(indicators.router, tags=["indicators"])
app.include_router(admin.router)
