"""
PNMP — PSSN Network Management Platform
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import os

from .core.config import settings
from .core.database import engine, Base, SessionLocal
from .api.router import api_router, ws_router
from .monitoring import init_scheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    
    # Create database tables (for development - use Alembic in production)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Initialize and start monitoring scheduler
    scheduler = init_scheduler(SessionLocal)
    await scheduler.start()
    logger.info("Monitoring scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PNMP...")
    await scheduler.stop()
    logger.info("Monitoring scheduler stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="PSSN Network Management Platform - Enterprise NMS API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "PSSN Network Management Platform",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns status of application, database, and monitoring worker.
    """
    from .monitoring import get_scheduler
    
    db_status = "disconnected"
    monitoring_status = "not_started"
    
    try:
        # Test database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    # Check monitoring scheduler
    scheduler = get_scheduler()
    if scheduler and scheduler.running:
        monitoring_status = "running"
    elif scheduler:
        monitoring_status = "stopped"
    
    overall_status = "healthy" if db_status == "connected" else "unhealthy"
    
    return {
        "status": overall_status,
        "database": db_status,
        "monitoring_worker": monitoring_status,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_DEBUG
    )
