"""
PNMP Events API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models import User, EventLog, Device, AlertSeverity, EventType
from ...schemas import EventResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = 0,
    limit: int = 100,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    device_id: Optional[int] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all events with optional filters"""
    query = db.query(EventLog)
    
    if device_id:
        query = query.filter(EventLog.device_id == device_id)
    if event_type:
        query = query.filter(EventLog.event_type == event_type)
    if severity:
        query = query.filter(EventLog.severity == severity)
    
    # Order by timestamp descending
    query = query.order_by(EventLog.timestamp.desc())
    
    # Pagination
    if page and page_size:
        offset = (page - 1) * page_size
        events = query.offset(offset).limit(page_size).all()
    else:
        events = query.offset(skip).limit(limit).all()
    
    # Build response with device name
    result = []
    for event in events:
        device = db.query(Device).filter(Device.id == event.device_id).first() if event.device_id else None
        result.append({
            "id": event.id,
            "device_id": event.device_id,
            "device_name": device.display_name if device else None,
            "interface_id": event.interface_id,
            "event_type": event.event_type,
            "category": event.event_type.value if event.event_type else None,  # Backward compat
            "severity": event.severity,
            "message": event.message,
            "source": event.source,
            "timestamp": event.timestamp
        })
    
    return result


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event by ID"""
    event = db.query(EventLog).filter(EventLog.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    device = db.query(Device).filter(Device.id == event.device_id).first() if event.device_id else None
    
    return {
        "id": event.id,
        "device_id": event.device_id,
        "device_name": device.display_name if device else None,
        "interface_id": event.interface_id,
        "event_type": event.event_type,
        "category": event.event_type.value if event.event_type else None,
        "severity": event.severity,
        "message": event.message,
        "source": event.source,
        "timestamp": event.timestamp
    }
