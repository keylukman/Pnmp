"""
PNMP Database Models
SQLAlchemy ORM models for all entities
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from ..core.database import Base


# ==================== ENUMS ====================

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    NETWORK_ENGINEER = "network_engineer"
    OPERATOR = "operator"
    VIEWER = "viewer"


class DeviceStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    WARNING = "warning"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class DeviceRole(str, enum.Enum):
    CORE_SWITCH = "core_switch"
    DISTRIBUTION_SWITCH = "distribution_switch"
    ACCESS_SWITCH = "access_switch"
    ROUTER = "router"
    FIREWALL = "firewall"
    WIRELESS_CONTROLLER = "wireless_controller"
    ACCESS_POINT = "access_point"
    SERVER = "server"
    LOAD_BALANCER = "load_balancer"
    OTHER = "other"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


# ==================== MODELS ====================

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")


class Site(Base):
    """Site/Location model"""
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    devices = relationship("Device", back_populates="site")


class Device(Base):
    """Network Device model"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(100), nullable=False, index=True)
    display_name = Column(String(150), nullable=False)
    management_ip = Column(String(45), nullable=False)  # Support IPv6
    vendor = Column(String(50), nullable=False)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=False)
    device_role = Column(SQLEnum(DeviceRole), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    location = Column(String(200), nullable=True)  # Floor, Rack, Room
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.UNKNOWN, nullable=False)
    monitoring_enabled = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    firmware_version = Column(String(50), nullable=True)
    mac_address = Column(String(17), nullable=True)
    uptime = Column(String(50), nullable=True)
    cpu_usage = Column(Integer, nullable=True)
    memory_usage = Column(Integer, nullable=True)
    temperature = Column(Integer, nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    site = relationship("Site", back_populates="devices")
    credentials = relationship("DeviceCredential", back_populates="device", cascade="all, delete-orphan")
    interfaces = relationship("DeviceInterface", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device")
    events = relationship("EventLog", back_populates="device")


class DeviceCredential(Base):
    """Device credentials (encrypted)"""
    __tablename__ = "device_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(100), nullable=True)
    encrypted_password = Column(Text, nullable=True)  # Encrypted
    snmp_version = Column(String(10), default="v2c", nullable=True)
    snmp_community_encrypted = Column(Text, nullable=True)  # Encrypted
    ssh_enabled = Column(Boolean, default=False)
    api_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="credentials")


class DeviceInterface(Base):
    """Network interface on a device"""
    __tablename__ = "device_interfaces"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    status = Column(String(20), default="down", nullable=False)
    speed = Column(String(20), nullable=True)
    rx_bytes = Column(Integer, default=0)
    tx_bytes = Column(Integer, default=0)
    rx_errors = Column(Integer, default=0)
    tx_errors = Column(Integer, default=0)
    rx_discards = Column(Integer, default=0)
    tx_discards = Column(Integer, default=0)
    utilization = Column(Integer, default=0)
    last_polled = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="interfaces")


class Alert(Base):
    """Alert/Incident model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="alerts")


class EventLog(Base):
    """Event log for audit and monitoring"""
    __tablename__ = "event_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    category = Column(String(50), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="events")


class AuditLog(Base):
    """Audit log for user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class TopologyLink(Base):
    """Network topology links (LLDP/CDP/Manual)"""
    __tablename__ = "topology_links"
    
    id = Column(Integer, primary_key=True, index=True)
    source_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    source_interface = Column(String(50), nullable=False)
    target_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    target_interface = Column(String(50), nullable=False)
    link_type = Column(String(20), default="manual", nullable=False)  # lldp, cdp, manual
    bandwidth = Column(String(20), nullable=True)
    status = Column(String(20), default="up", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
