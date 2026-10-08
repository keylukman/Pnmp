"""
Metrics API Routes
Provides historical metrics for devices and interfaces
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models import User, Device, DeviceInterface, DeviceMetric, InterfaceMetric
from ...schemas import DeviceMetricResponse, InterfaceMetricResponse, MetricsResponse, InterfaceMetricsResponse

router = APIRouter(tags=["Metrics"])


@router.get("/devices/{device_id}/metrics", response_model=MetricsResponse)
async def get_device_metrics(
    device_id: int,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical device metrics (CPU, memory, temperature, uptime).
    
    Query parameters:
    - from: Start datetime (default: 24 hours ago)
    - to: End datetime (default: now)
    - limit: Maximum number of records (default: 100)
    """
    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Set default time range
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(hours=24)
    
    # Query metrics
    metrics = db.query(DeviceMetric).filter(
        DeviceMetric.device_id == device_id,
        DeviceMetric.timestamp >= from_date,
        DeviceMetric.timestamp <= to_date
    ).order_by(DeviceMetric.timestamp.desc()).limit(limit).all()
    
    return MetricsResponse(
        device_id=device_id,
        metrics=[
            DeviceMetricResponse(
                timestamp=m.timestamp,
                cpu_percent=m.cpu_percent,
                memory_percent=m.memory_percent,
                temperature=m.temperature,
                uptime_seconds=m.uptime_seconds
            )
            for m in metrics
        ]
    )


@router.get("/interfaces/{interface_id}/metrics", response_model=InterfaceMetricsResponse)
async def get_interface_metrics(
    interface_id: int,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical interface metrics (traffic, errors, utilization).
    
    Query parameters:
    - from: Start datetime (default: 24 hours ago)
    - to: End datetime (default: now)
    - limit: Maximum number of records (default: 100)
    """
    # Verify interface exists
    interface = db.query(DeviceInterface).filter(DeviceInterface.id == interface_id).first()
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interface not found"
        )
    
    # Set default time range
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(hours=24)
    
    # Query metrics
    metrics = db.query(InterfaceMetric).filter(
        InterfaceMetric.interface_id == interface_id,
        InterfaceMetric.timestamp >= from_date,
        InterfaceMetric.timestamp <= to_date
    ).order_by(InterfaceMetric.timestamp.desc()).limit(limit).all()
    
    return InterfaceMetricsResponse(
        interface_id=interface_id,
        metrics=[
            InterfaceMetricResponse(
                timestamp=m.timestamp,
                rx_bps=m.rx_bps,
                tx_bps=m.tx_bps,
                rx_errors=m.rx_errors,
                tx_errors=m.tx_errors,
                utilization_in=m.utilization_in,
                utilization_out=m.utilization_out
            )
            for m in metrics
        ]
    )
