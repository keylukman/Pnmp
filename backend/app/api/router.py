"""
PNMP API Router
Aggregates all v1 API routes
"""
from fastapi import APIRouter
from .v1 import auth, users, sites, devices

api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(sites.router)
api_router.include_router(devices.router)
