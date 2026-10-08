"""
PNMP Pydantic Schemas
Request/Response validation schemas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from ..models.models import (
    UserRole, DeviceStatus, DeviceRole, AlertSeverity, AlertStatus,
    MonitoringMethod, InterfaceStatus, EventType
)


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
    monitoring_method: MonitoringMethod = MonitoringMethod.NONE


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
    monitoring_method: Optional[MonitoringMethod] = None
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
    failure_count: int = 0
    site_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== CREDENTIAL SCHEMAS ====================

class DeviceCredentialCreate(BaseModel):
    """Request schema for creating/updating device credentials"""
    # SSH/API credentials
    username: Optional[str] = None
    password: Optional[str] = None
    
    # SNMP v2c
    snmp_version: str = "v2c"
    snmp_community: Optional[str] = None
    
    # SNMP v3
    snmp_username: Optional[str] = None
    snmp_auth_protocol: Optional[str] = None  # MD5, SHA, SHA256
    snmp_auth_password: Optional[str] = None
    snmp_privacy_protocol: Optional[str] = None  # DES, AES
    snmp_privacy_password: Optional[str] = None
    
    # Connection flags
    ssh_enabled: bool = False
    api_enabled: bool = False
    snmp_enabled: bool = True
    
    @field_validator('snmp_auth_protocol')
    @classmethod
    def validate_auth_protocol(cls, v):
        if v and v.upper() not in ['MD5', 'SHA', 'SHA256', 'SHA-256']:
            raise ValueError('snmp_auth_protocol must be MD5, SHA, or SHA256')
        return v.upper() if v else v
    
    @field_validator('snmp_privacy_protocol')
    @classmethod
    def validate_privacy_protocol(cls, v):
        if v and v.upper() not in ['DES', 'AES', 'AES128', 'AES192', 'AES256']:
            raise ValueError('snmp_privacy_protocol must be DES or AES')
        return v.upper() if v else v


class DeviceCredentialSafeResponse(BaseModel):
    """
    SAFE response - never exposes actual secrets.
    Only shows whether credentials are configured.
    """
    device_id: int
    username_configured: bool = False
    password_configured: bool = False
    snmp_configured: bool = False
    snmp_version: Optional[str] = None
    snmp_v3_configured: bool = False
    ssh_enabled: bool = False
    api_enabled: bool = False
    snmp_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== INTERFACE SCHEMAS ====================

class InterfaceResponse(BaseModel):
    id: int
    device_id: int
    if_index: Optional[int] = None
    name: str
    description: Optional[str] = None
    alias: Optional[str] = None
    status: InterfaceStatus
    admin_status: Optional[InterfaceStatus] = None
    speed: Optional[str] = None
    speed_bps: Optional[int] = None
    duplex: Optional[str] = None
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_errors: int = 0
    tx_errors: int = 0
    rx_discards: int = 0
    tx_discards: int = 0
    rx_bps: int = 0
    tx_bps: int = 0
    utilization: int = 0
    utilization_in: int = 0
    utilization_out: int = 0
    last_polled: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== CONNECTION TEST SCHEMAS ====================

class TestConnectionResponse(BaseModel):
    success: bool
    device_id: int
    method: Optional[str] = None
    latency_ms: Optional[float] = None
    message: str
    error_code: Optional[str] = None


# ==================== ALERT SCHEMAS ====================

class AlertResponse(BaseModel):
    id: int
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    interface_id: Optional[int] = None
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
    interface_id: Optional[int] = None
    event_type: EventType
    category: Optional[str] = None  # Kept for backward compatibility
    severity: AlertSeverity
    message: str
    source: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ==================== METRICS SCHEMAS ====================

class DeviceMetricResponse(BaseModel):
    timestamp: datetime
    cpu_percent: Optional[int] = None
    memory_percent: Optional[int] = None
    temperature: Optional[int] = None
    uptime_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


class InterfaceMetricResponse(BaseModel):
    timestamp: datetime
    rx_bps: int = 0
    tx_bps: int = 0
    rx_errors: int = 0
    tx_errors: int = 0
    utilization_in: int = 0
    utilization_out: int = 0
    
    class Config:
        from_attributes = True


class MetricsResponse(BaseModel):
    device_id: int
    metrics: List[DeviceMetricResponse]


class InterfaceMetricsResponse(BaseModel):
    interface_id: int
    metrics: List[InterfaceMetricResponse]


# ==================== DASHBOARD SCHEMAS ====================

class DashboardSummary(BaseModel):
    total_devices: int
    devices_up: int
    devices_down: int
    devices_warning: int
    devices_unknown: int
    devices_maintenance: int
    active_alerts: int
    total_sites: int


class DeviceStatusSummary(BaseModel):
    up: int
    down: int
    warning: int
    unknown: int
    maintenance: int


# ==================== PAGINATION SCHEMAS ====================

class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    success: bool = True
    data: List = []
    pagination: PaginationInfo


# ==================== GENERIC RESPONSE ====================

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None
