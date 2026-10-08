"""
PNMP Pydantic Schemas
Request/Response validation schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from ..models.models import UserRole, DeviceStatus, DeviceRole, AlertSeverity, AlertStatus


# ==================== AUTH SCHEMAS ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    hashed_password: str


# ==================== SITE SCHEMAS ====================

class SiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    address: Optional[str] = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None


class SiteResponse(SiteBase):
    id: int
    device_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== DEVICE SCHEMAS ====================

class DeviceBase(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=150)
    management_ip: str = Field(..., max_length=45)
    vendor: str = Field(..., max_length=50)
    model: Optional[str] = None
    serial_number: Optional[str] = None
    device_type: str = Field(..., max_length=50)
    device_role: DeviceRole
    site_id: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    monitoring_enabled: bool = True


class DeviceCreate(DeviceBase):
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None


class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    display_name: Optional[str] = None
    management_ip: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    device_type: Optional[str] = None
    device_role: Optional[DeviceRole] = None
    site_id: Optional[int] = None
    location: Optional[str] = None
    status: Optional[DeviceStatus] = None
    monitoring_enabled: Optional[bool] = None
    description: Optional[str] = None
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None


class DeviceResponse(DeviceBase):
    id: int
    status: DeviceStatus
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None
    uptime: Optional[str] = None
    cpu_usage: Optional[int] = None
    memory_usage: Optional[int] = None
    temperature: Optional[int] = None
    last_seen: Optional[datetime] = None
    site_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeviceCredentialCreate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    snmp_version: str = "v2c"
    snmp_community: Optional[str] = None
    ssh_enabled: bool = False
    api_enabled: bool = False


class DeviceCredentialResponse(BaseModel):
    id: int
    device_id: int
    username: Optional[str] = None
    snmp_version: str
    ssh_enabled: bool
    api_enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[float] = None


# ==================== ALERT SCHEMAS ====================

class AlertResponse(BaseModel):
    id: int
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    severity: AlertSeverity
    title: str
    description: Optional[str] = None
    source: str
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== EVENT SCHEMAS ====================

class EventResponse(BaseModel):
    id: int
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    category: str
    severity: AlertSeverity
    message: str
    source: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ==================== GENERIC RESPONSE ====================

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None
