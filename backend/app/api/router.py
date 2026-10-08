"""
PNMP API Router
Aggregates all v1 API routes and WebSocket endpoints
"""
from fastapi import APIRouter
from .v1 import auth, users, sites, devices, dashboard, alerts, events, metrics, integrations
from .ws import dashboard as ws_dashboard

api_router = APIRouter(prefix="/api/v1")

# Include all v1 routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(sites.router)
api_router.include_router(devices.router)
api_router.include_router(dashboard.router)
api_router.include_router(alerts.router)
api_router.include_router(events.router)
api_router.include_router(metrics.router)
api_router.include_router(integrations.router)

# WebSocket router (no prefix)
ws_router = APIRouter()
ws_router.include_router(ws_dashboard.router)
