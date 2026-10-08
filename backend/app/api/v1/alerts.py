"""
PNMP Alerts API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models import User, Alert, Device, AlertSeverity, AlertStatus
from ...schemas import AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = 0,
    limit: int = 100,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    device_id: Optional[int] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all alerts with optional filters"""
    query = db.query(Alert)
    
    if device_id:
        query = query.filter(Alert.device_id == device_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    
    # Order by created_at descending
    query = query.order_by(Alert.created_at.desc())
    
    # Pagination
    if page and page_size:
        offset = (page - 1) * page_size
        alerts = query.offset(offset).limit(page_size).all()
    else:
        alerts = query.offset(skip).limit(limit).all()
    
    # Build response with device name
    result = []
    for alert in alerts:
        device = db.query(Device).filter(Device.id == alert.device_id).first() if alert.device_id else None
        result.append({
            "id": alert.id,
            "device_id": alert.device_id,
            "device_name": device.display_name if device else None,
            "interface_id": alert.interface_id,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "source": alert.source,
            "status": alert.status,
            "created_at": alert.created_at,
            "acknowledged_at": alert.acknowledged_at,
            "resolved_at": alert.resolved_at
        })
    
    return result


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alert by ID"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    device = db.query(Device).filter(Device.id == alert.device_id).first() if alert.device_id else None
    
    return {
        "id": alert.id,
        "device_id": alert.device_id,
        "device_name": device.display_name if device else None,
        "interface_id": alert.interface_id,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "source": alert.source,
        "status": alert.status,
        "created_at": alert.created_at,
        "acknowledged_at": alert.acknowledged_at,
        "resolved_at": alert.resolved_at
    }


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot acknowledge a resolved alert"
        )
    
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.id
    db.commit()
    db.refresh(alert)
    
    device = db.query(Device).filter(Device.id == alert.device_id).first() if alert.device_id else None
    
    return {
        "id": alert.id,
        "device_id": alert.device_id,
        "device_name": device.display_name if device else None,
        "interface_id": alert.interface_id,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "source": alert.source,
        "status": alert.status,
        "created_at": alert.created_at,
        "acknowledged_at": alert.acknowledged_at,
        "resolved_at": alert.resolved_at
    }


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id
    db.commit()
    db.refresh(alert)
    
    device = db.query(Device).filter(Device.id == alert.device_id).first() if alert.device_id else None
    
    return {
        "id": alert.id,
        "device_id": alert.device_id,
        "device_name": device.display_name if device else None,
        "interface_id": alert.interface_id,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "source": alert.source,
        "status": alert.status,
        "created_at": alert.created_at,
        "acknowledged_at": alert.acknowledged_at,
        "resolved_at": alert.resolved_at
    }
