"""
PNMP Dashboard API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models import User, Device, Site, Alert, DeviceStatus, AlertStatus
from ...schemas import DashboardSummary, DeviceStatusSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard summary with device counts and active alerts.
    Data comes from database, not hardcoded.
    """
    # Device counts by status
    total_devices = db.query(Device).count()
    devices_up = db.query(Device).filter(Device.status == DeviceStatus.UP).count()
    devices_down = db.query(Device).filter(Device.status == DeviceStatus.DOWN).count()
    devices_warning = db.query(Device).filter(Device.status == DeviceStatus.WARNING).count()
    devices_unknown = db.query(Device).filter(Device.status == DeviceStatus.UNKNOWN).count()
    devices_maintenance = db.query(Device).filter(Device.status == DeviceStatus.MAINTENANCE).count()
    
    # Active alerts (open or acknowledged)
    active_alerts = db.query(Alert).filter(
        Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED])
    ).count()
    
    # Total sites
    total_sites = db.query(Site).count()
    
    return DashboardSummary(
        total_devices=total_devices,
        devices_up=devices_up,
        devices_down=devices_down,
        devices_warning=devices_warning,
        devices_unknown=devices_unknown,
        devices_maintenance=devices_maintenance,
        active_alerts=active_alerts,
        total_sites=total_sites
    )


@router.get("/device-status", response_model=DeviceStatusSummary)
async def get_device_status_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get device status distribution.
    """
    return DeviceStatusSummary(
        up=db.query(Device).filter(Device.status == DeviceStatus.UP).count(),
        down=db.query(Device).filter(Device.status == DeviceStatus.DOWN).count(),
        warning=db.query(Device).filter(Device.status == DeviceStatus.WARNING).count(),
        unknown=db.query(Device).filter(Device.status == DeviceStatus.UNKNOWN).count(),
        maintenance=db.query(Device).filter(Device.status == DeviceStatus.MAINTENANCE).count()
    )
