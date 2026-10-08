"""
Monitoring API Routes
Provides monitoring status and control endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models import User
from ...monitoring import get_scheduler

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/status", response_model=Dict[str, Any])
async def get_monitoring_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get monitoring scheduler status and statistics.
    
    Returns:
    - running: Whether scheduler is running
    - interval: Polling interval in seconds
    - max_concurrency: Maximum concurrent polls
    - active_polls: Currently active polls
    - total_polls: Total polls since startup
    - successful_polls: Successful polls count
    - failed_polls: Failed polls count
    - last_poll: Timestamp of last poll cycle
    """
    scheduler = get_scheduler()
    
    if not scheduler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring scheduler not initialized"
        )
    
    return scheduler.get_status()
