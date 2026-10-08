"""
PNMP Devices API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models import User, Device, DeviceCredential, Site
from ...schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    DeviceCredentialCreate, DeviceCredentialResponse, TestConnectionResponse
)

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    site_id: Optional[int] = None,
    device_role: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all devices with optional filters"""
    query = db.query(Device)
    
    # Apply filters
    if site_id:
        query = query.filter(Device.site_id == site_id)
    if device_role:
        query = query.filter(Device.device_role == device_role)
    if status_filter:
        query = query.filter(Device.status == status_filter)
    if search:
        query = query.filter(
            (Device.display_name.ilike(f"%{search}%")) |
            (Device.hostname.ilike(f"%{search}%")) |
            (Device.management_ip.ilike(f"%{search}%"))
        )
    
    devices = query.offset(skip).limit(limit).all()
    
    # Build response with site name
    result = []
    for device in devices:
        site = db.query(Site).filter(Site.id == device.site_id).first() if device.site_id else None
        device_dict = {
            "id": device.id,
            "hostname": device.hostname,
            "display_name": device.display_name,
            "management_ip": device.management_ip,
            "vendor": device.vendor,
            "model": device.model,
            "serial_number": device.serial_number,
            "device_type": device.device_type,
            "device_role": device.device_role,
            "site_id": device.site_id,
            "site_name": site.name if site else None,
            "location": device.location,
            "status": device.status,
            "monitoring_enabled": device.monitoring_enabled,
            "description": device.description,
            "firmware_version": device.firmware_version,
            "mac_address": device.mac_address,
            "uptime": device.uptime,
            "cpu_usage": device.cpu_usage,
            "memory_usage": device.memory_usage,
            "temperature": device.temperature,
            "last_seen": device.last_seen,
            "created_at": device.created_at,
            "updated_at": device.updated_at
        }
        result.append(device_dict)
    
    return result


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new device"""
    # Verify site exists if provided
    if device_data.site_id:
        site = db.query(Site).filter(Site.id == device_data.site_id).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site not found"
            )
    
    # Create device
    db_device = Device(
        hostname=device_data.hostname,
        display_name=device_data.display_name,
        management_ip=device_data.management_ip,
        vendor=device_data.vendor,
        model=device_data.model,
        serial_number=device_data.serial_number,
        device_type=device_data.device_type,
        device_role=device_data.device_role,
        site_id=device_data.site_id,
        location=device_data.location,
        description=device_data.description,
        monitoring_enabled=device_data.monitoring_enabled,
        firmware_version=device_data.firmware_version,
        mac_address=device_data.mac_address,
        status="unknown"
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    # Get site name
    site = db.query(Site).filter(Site.id == db_device.site_id).first() if db_device.site_id else None
    
    return {
        "id": db_device.id,
        "hostname": db_device.hostname,
        "display_name": db_device.display_name,
        "management_ip": db_device.management_ip,
        "vendor": db_device.vendor,
        "model": db_device.model,
        "serial_number": db_device.serial_number,
        "device_type": db_device.device_type,
        "device_role": db_device.device_role,
        "site_id": db_device.site_id,
        "site_name": site.name if site else None,
        "location": db_device.location,
        "status": db_device.status,
        "monitoring_enabled": db_device.monitoring_enabled,
        "description": db_device.description,
        "firmware_version": db_device.firmware_version,
        "mac_address": db_device.mac_address,
        "uptime": db_device.uptime,
        "cpu_usage": db_device.cpu_usage,
        "memory_usage": db_device.memory_usage,
        "temperature": db_device.temperature,
        "last_seen": db_device.last_seen,
        "created_at": db_device.created_at,
        "updated_at": db_device.updated_at
    }


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device by ID"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    site = db.query(Site).filter(Site.id == device.site_id).first() if device.site_id else None
    
    return {
        "id": device.id,
        "hostname": device.hostname,
        "display_name": device.display_name,
        "management_ip": device.management_ip,
        "vendor": device.vendor,
        "model": device.model,
        "serial_number": device.serial_number,
        "device_type": device.device_type,
        "device_role": device.device_role,
        "site_id": device.site_id,
        "site_name": site.name if site else None,
        "location": device.location,
        "status": device.status,
        "monitoring_enabled": device.monitoring_enabled,
        "description": device.description,
        "firmware_version": device.firmware_version,
        "mac_address": device.mac_address,
        "uptime": device.uptime,
        "cpu_usage": device.cpu_usage,
        "memory_usage": device.memory_usage,
        "temperature": device.temperature,
        "last_seen": device.last_seen,
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update device"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update fields
    update_data = device_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(device, key, value)
    
    db.commit()
    db.refresh(device)
    
    site = db.query(Site).filter(Site.id == device.site_id).first() if device.site_id else None
    
    return {
        "id": device.id,
        "hostname": device.hostname,
        "display_name": device.display_name,
        "management_ip": device.management_ip,
        "vendor": device.vendor,
        "model": device.model,
        "serial_number": device.serial_number,
        "device_type": device.device_type,
        "device_role": device.device_role,
        "site_id": device.site_id,
        "site_name": site.name if site else None,
        "location": device.location,
        "status": device.status,
        "monitoring_enabled": device.monitoring_enabled,
        "description": device.description,
        "firmware_version": device.firmware_version,
        "mac_address": device.mac_address,
        "uptime": device.uptime,
        "cpu_usage": device.cpu_usage,
        "memory_usage": device.memory_usage,
        "temperature": device.temperature,
        "last_seen": device.last_seen,
        "created_at": device.created_at,
        "updated_at": device.updated_at
    }


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete device"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    db.delete(device)
    db.commit()


@router.post("/{device_id}/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test connectivity to device (ping)"""
    import subprocess
    import time
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Simple ping test
    start_time = time.time()
    try:
        # Windows ping
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "3000", device.management_ip],
            capture_output=True, text=True, timeout=5
        )
        latency = (time.time() - start_time) * 1000
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Device {device.management_ip} is reachable",
                "latency_ms": round(latency, 2)
            }
        else:
            return {
                "success": False,
                "message": f"Device {device.management_ip} is not reachable",
                "latency_ms": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "latency_ms": None
        }


@router.post("/{device_id}/credentials", response_model=DeviceCredentialResponse)
async def set_credentials(
    device_id: int,
    cred_data: DeviceCredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set device credentials (encrypted)"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # TODO: Encrypt password and SNMP community before storing
    # For now, store as-is (will be encrypted in production)
    
    # Delete existing credentials
    db.query(DeviceCredential).filter(DeviceCredential.device_id == device_id).delete()
    
    # Create new credentials
    db_cred = DeviceCredential(
        device_id=device_id,
        username=cred_data.username,
        encrypted_password=cred_data.password,  # TODO: Encrypt
        snmp_version=cred_data.snmp_version,
        snmp_community_encrypted=cred_data.snmp_community,  # TODO: Encrypt
        ssh_enabled=cred_data.ssh_enabled,
        api_enabled=cred_data.api_enabled
    )
    db.add(db_cred)
    db.commit()
    db.refresh(db_cred)
    
    return db_cred


@router.get("/{device_id}/credentials", response_model=DeviceCredentialResponse)
async def get_credentials(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device credentials (without sensitive data)"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    cred = db.query(DeviceCredential).filter(DeviceCredential.device_id == device_id).first()
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No credentials configured"
        )
    
    return cred
