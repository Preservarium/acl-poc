from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import engine
from app.models import Base
from app.api import auth, permissions, sites, plans, sensors, users, groups, brokers, alarms, alerts, dashboards, audit_logs, cache as cache_api, system_config
from app.tasks.scheduler import start_scheduler, shutdown_scheduler
from app.services.cache_service import cache
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Startup: Connect to Redis cache
    await cache.connect()
    logger.info("Cache service initialized")

    # Start background scheduler if enabled
    if settings.ENABLE_SCHEDULER:
        try:
            start_scheduler()
            logger.info("Background scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")

    yield

    # Shutdown: Stop scheduler
    if settings.ENABLE_SCHEDULER:
        try:
            shutdown_scheduler()
            logger.info("Background scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")

    # Shutdown: Disconnect from Redis
    await cache.disconnect()
    logger.info("Cache service disconnected")


# Create FastAPI app
app = FastAPI(
    title="ACL PoC API",
    description="Pure ACL system with hybrid inheritance proof-of-concept",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ACL PoC API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(permissions.router, prefix="/api")
app.include_router(sites.router, prefix="/api")
app.include_router(plans.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")
app.include_router(brokers.router, prefix="/api")
app.include_router(alarms.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboards.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(audit_logs.router, prefix="/api")
app.include_router(cache_api.router, prefix="/api")
app.include_router(system_config.router, prefix="/api")
