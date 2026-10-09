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


class MonitoringMethod(str, enum.Enum):
    SNMP = "snmp"
    REST_API = "rest_api"
    SSH = "ssh"
    ZABBIX = "zabbix"
    MULTI = "multi"
    NONE = "none"


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
    monitoring_method = Column(SQLEnum(MonitoringMethod), default=MonitoringMethod.NONE, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)  # For status calculation
    poll_interval = Column(Integer, default=60, nullable=False)  # Per-device polling interval in seconds
    last_polled = Column(DateTime(timezone=True), nullable=True)  # Last successful poll time
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
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # SSH/API credentials
    username = Column(String(100), nullable=True)
    encrypted_password = Column(Text, nullable=True)  # AES encrypted
    
    # SNMP v2c
    snmp_version = Column(String(10), default="v2c", nullable=True)
    snmp_community_encrypted = Column(Text, nullable=True)  # AES encrypted
    
    # SNMP v3
    snmp_username = Column(String(100), nullable=True)
    snmp_auth_protocol = Column(String(10), nullable=True)  # MD5, SHA, SHA256
    snmp_auth_password_encrypted = Column(Text, nullable=True)  # AES encrypted
    snmp_privacy_protocol = Column(String(10), nullable=True)  # DES, AES
    snmp_privacy_password_encrypted = Column(Text, nullable=True)  # AES encrypted
    
    # Connection flags
    ssh_enabled = Column(Boolean, default=False)
    api_enabled = Column(Boolean, default=False)
    snmp_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="credentials")


class InterfaceStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    ADMIN_DOWN = "admin_down"
    TESTING = "testing"
    UNKNOWN = "unknown"


class DeviceInterface(Base):
    """Network interface on a device"""
    __tablename__ = "device_interfaces"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    if_index = Column(Integer, nullable=True)  # SNMP ifIndex
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    alias = Column(String(200), nullable=True)  # ifAlias
    status = Column(SQLEnum(InterfaceStatus), default=InterfaceStatus.UNKNOWN, nullable=False)
    admin_status = Column(SQLEnum(InterfaceStatus), default=InterfaceStatus.UNKNOWN, nullable=True)
    speed = Column(String(20), nullable=True)  # e.g., "1Gbps", "10Gbps"
    speed_bps = Column(Integer, nullable=True)  # Speed in bits per second
    duplex = Column(String(10), nullable=True)  # full, half
    mtu = Column(Integer, nullable=True)
    
    # Current counters
    rx_bytes = Column(Integer, default=0)  # 64-bit counter
    tx_bytes = Column(Integer, default=0)  # 64-bit counter
    rx_errors = Column(Integer, default=0)
    tx_errors = Column(Integer, default=0)
    rx_discards = Column(Integer, default=0)
    tx_discards = Column(Integer, default=0)
    
    # Calculated rates (bits per second)
    rx_bps = Column(Integer, default=0)
    tx_bps = Column(Integer, default=0)
    
    # Utilization percentage
    utilization = Column(Integer, default=0)  # max of in/out
    utilization_in = Column(Integer, default=0)
    utilization_out = Column(Integer, default=0)
    
    last_polled = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="interfaces")


class Alert(Base):
    """Alert/Incident model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    interface_id = Column(Integer, ForeignKey("device_interfaces.id", ondelete="SET NULL"), nullable=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=False)  # monitoring, snmp, api, system
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    interface = relationship("DeviceInterface")


class EventType(str, enum.Enum):
    DEVICE_DOWN = "device_down"
    DEVICE_UP = "device_up"
    DEVICE_WARNING = "device_warning"
    INTERFACE_DOWN = "interface_down"
    INTERFACE_UP = "interface_up"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    HIGH_UTILIZATION = "high_utilization"
    HIGH_TEMPERATURE = "high_temperature"
    SNMP_TIMEOUT = "snmp_timeout"
    API_TIMEOUT = "api_timeout"
    SSH_TIMEOUT = "ssh_timeout"
    CONFIG_CHANGE = "config_change"
    AUTH_FAILURE = "auth_failure"
    LINK_FLAPPING = "link_flapping"
    BGP_PEER_DOWN = "bgp_peer_down"
    BGP_PEER_UP = "bgp_peer_up"
    OTHER = "other"


class EventLog(Base):
    """Event log for audit and monitoring"""
    __tablename__ = "event_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    interface_id = Column(Integer, ForeignKey("device_interfaces.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)  # monitoring, snmp, api, system
    metadata_json = Column(Text, nullable=True)  # Additional context as JSON
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    device = relationship("Device", back_populates="events")
    interface = relationship("DeviceInterface")


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


# ==================== METRICS MODELS ====================

class DeviceMetric(Base):
    """Historical device performance metrics"""
    __tablename__ = "device_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Performance metrics
    cpu_percent = Column(Integer, nullable=True)  # 0-100
    memory_percent = Column(Integer, nullable=True)  # 0-100
    temperature = Column(Integer, nullable=True)  # Celsius
    uptime_seconds = Column(Integer, nullable=True)
    
    # Collection metadata
    collection_method = Column(String(20), nullable=True)  # snmp, api, ssh
    response_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InterfaceMetric(Base):
    """Historical interface performance metrics"""
    __tablename__ = "interface_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    interface_id = Column(Integer, ForeignKey("device_interfaces.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Traffic counters (absolute values)
    rx_bytes = Column(Integer, default=0)
    tx_bytes = Column(Integer, default=0)
    rx_errors = Column(Integer, default=0)
    tx_errors = Column(Integer, default=0)
    rx_discards = Column(Integer, default=0)
    tx_discards = Column(Integer, default=0)
    
    # Calculated rates (bits per second)
    rx_bps = Column(Integer, default=0)
    tx_bps = Column(Integer, default=0)
    
    # Utilization percentage
    utilization_in = Column(Integer, default=0)
    utilization_out = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
