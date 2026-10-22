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
from pathlib import Path
from fastapi.responses import JSONResponse

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
    from sqlalchemy import text
    from .monitoring import get_scheduler
    
    db_status = "disconnected"
    monitoring_status = "not_started"
    
    try:
        # Test database connection
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        db_status = "connected"
    except Exception as e:
        # Never leak exception details/stack traces in the response
        logger.error("Database health check failed")
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


# ---------------------------------------------------------------------------
# Static frontend serving (single-origin deployment on Windows).
# If a production build exists (repo_root/dist), the backend serves it so the
# user opens ONE URL (http://127.0.0.1:8000) and there are no CORS issues at
# all. Mounted AFTER API routes so /api/v1, /health, /docs keep priority.
# SPA fallback: unknown non-API paths return index.html so deep links like
# /devices survive a browser refresh.
# ---------------------------------------------------------------------------
def _mount_frontend(app: FastAPI) -> None:
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    candidates = [
        Path(__file__).resolve().parent.parent.parent / "dist",  # repo_root/dist
        Path.cwd() / "dist",
    ]
    dist_dir = next((d for d in candidates if (d / "index.html").is_file()), None)
    if dist_dir is None:
        logger.info("No frontend build found in dist/ — API-only mode (run `npm run build`)")
        return

    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    dist_root = dist_dir.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # Never shadow real API/ws/docs paths; serve file if it exists, else SPA shell.
        if full_path.startswith(("api", "ws", "docs", "openapi.json", "health")):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        # Path-traversal guard: reject any parent-directory segment, then verify
        # the resolved target is strictly inside the build directory.
        if ".." in full_path.split("/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = (dist_dir / full_path).resolve()
        if (
            full_path
            and file_path.is_file()
            and file_path != dist_root
            and str(file_path).startswith(str(dist_root) + os.sep)
        ):
            return FileResponse(str(file_path))
        return FileResponse(str(dist_dir / "index.html"))

    # Override the JSON root banner with the SPA shell so a single origin
    # (http://127.0.0.1:8000) opens the dashboard directly.
    from starlette.routing import Route

    async def spa_root(request):
        return FileResponse(str(dist_dir / "index.html"))

    for i, rt in enumerate(app.router.routes):
        if isinstance(rt, Route) and rt.path == "/" and "GET" in getattr(rt, "methods", set()):
            app.router.routes[i] = Route("/", endpoint=spa_root, methods=["GET"])
            break

    logger.info(f"Serving frontend build from {dist_dir}")


_mount_frontend(app)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_DEBUG
    )
